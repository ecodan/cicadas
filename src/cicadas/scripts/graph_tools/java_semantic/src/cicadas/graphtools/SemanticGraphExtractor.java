package cicadas.graphtools;

import com.sun.source.tree.ClassTree;
import com.sun.source.tree.CompilationUnitTree;
import com.sun.source.tree.ImportTree;
import com.sun.source.tree.MethodInvocationTree;
import com.sun.source.tree.MethodTree;
import com.sun.source.tree.NewClassTree;
import com.sun.source.tree.Tree;
import com.sun.source.util.JavacTask;
import com.sun.source.util.TreePath;
import com.sun.source.util.TreePathScanner;
import com.sun.source.util.Trees;
import java.io.IOException;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Deque;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.TreeSet;
import javax.lang.model.element.Element;
import javax.lang.model.element.ElementKind;
import javax.lang.model.element.ExecutableElement;
import javax.lang.model.element.PackageElement;
import javax.lang.model.element.TypeElement;
import javax.lang.model.util.Elements;
import javax.tools.DiagnosticCollector;
import javax.tools.JavaCompiler;
import javax.tools.JavaFileObject;
import javax.tools.StandardJavaFileManager;
import javax.tools.ToolProvider;

public final class SemanticGraphExtractor {
    private SemanticGraphExtractor() {}

    public static void main(String[] args) throws Exception {
        Config config = Config.parse(args);
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        if (compiler == null) {
            System.err.println("No system Java compiler available.");
            System.exit(2);
        }

        List<Path> sourceRoots = readPathList(config.sourceRootsFile);
        List<Path> javaFiles = readPathList(config.filesFile);
        if (javaFiles.isEmpty()) {
            return;
        }

        DiagnosticCollector<JavaFileObject> diagnostics = new DiagnosticCollector<>();
        try (StandardJavaFileManager fileManager = compiler.getStandardFileManager(diagnostics, Locale.ROOT, StandardCharsets.UTF_8)) {
            Iterable<? extends JavaFileObject> units = fileManager.getJavaFileObjectsFromPaths(javaFiles);
            List<String> options = new ArrayList<>(Arrays.asList("-proc:none", "-implicit:none"));
            if (!sourceRoots.isEmpty()) {
                options.add("-sourcepath");
                options.add(joinPaths(sourceRoots));
            }
            if (config.classpath != null && !config.classpath.isBlank()) {
                options.add("-classpath");
                options.add(config.classpath);
            }

            JavacTask task = (JavacTask) compiler.getTask(null, fileManager, diagnostics, options, null, units);
            List<CompilationUnitTree> compilationUnits = new ArrayList<>();
            for (CompilationUnitTree unit : task.parse()) {
                compilationUnits.add(unit);
            }
            try {
                task.analyze();
            } catch (Throwable ignored) {
                // Partial attribution is still useful for graphing.
            }

            Trees trees = Trees.instance(task);
            Elements elements = task.getElements();
            try (PrintWriter out = new PrintWriter(Files.newBufferedWriter(config.output, StandardCharsets.UTF_8))) {
                for (CompilationUnitTree unit : compilationUnits) {
                    String relPath = relativize(config.root, Paths.get(unit.getSourceFile().toUri()));
                    GraphScanner scanner = new GraphScanner(trees, elements, unit, relPath, out);
                    scanner.scan(unit, null);
                }
            }
        }
    }

    private static List<Path> readPathList(Path path) throws IOException {
        List<Path> values = new ArrayList<>();
        if (!Files.exists(path)) {
            return values;
        }
        for (String line : Files.readAllLines(path, StandardCharsets.UTF_8)) {
            String trimmed = line.trim();
            if (!trimmed.isEmpty()) {
                values.add(Paths.get(trimmed));
            }
        }
        return values;
    }

    private static String joinPaths(List<Path> paths) {
        List<String> values = new ArrayList<>(paths.size());
        for (Path path : paths) {
            values.add(path.toString());
        }
        return String.join(System.getProperty("path.separator"), values);
    }

    private static String relativize(Path root, Path file) {
        try {
            return root.relativize(file).toString().replace('\\', '/');
        } catch (IllegalArgumentException ignored) {
            return file.toString().replace('\\', '/');
        }
    }

    private static String methodSymbolName(ExecutableElement element) {
        Element enclosing = element.getEnclosingElement();
        String owner = symbolName(enclosing);
        String methodName = element.getKind() == ElementKind.CONSTRUCTOR ? "<init>" : element.getSimpleName().toString();
        List<String> params = new ArrayList<>();
        try {
            element.getParameters().forEach(param -> {
                try {
                    params.add(param.asType() == null ? "unknown" : param.asType().toString());
                } catch (RuntimeException ignored) {
                    params.add("unknown");
                }
            });
        } catch (RuntimeException ignored) {
            return owner + "#" + methodName;
        }
        return owner + "#" + methodName + "(" + String.join(",", params) + ")";
    }

    private static String symbolName(Element element) {
        if (element == null) {
            return "";
        }
        if (element instanceof ExecutableElement executableElement) {
            return methodSymbolName(executableElement);
        }
        if (element instanceof TypeElement typeElement) {
            return typeElement.getQualifiedName().toString();
        }
        if (element instanceof PackageElement packageElement) {
            return packageElement.getQualifiedName().toString();
        }
        return element.toString();
    }

    private static String sanitize(String value) {
        return value == null ? "" : value.replace("\t", " ").replace("\n", " ").replace("\r", " ");
    }

    private static final class Config {
        final Path root;
        final Path output;
        final Path filesFile;
        final Path sourceRootsFile;
        final String classpath;

        private Config(Path root, Path output, Path filesFile, Path sourceRootsFile, String classpath) {
            this.root = root;
            this.output = output;
            this.filesFile = filesFile;
            this.sourceRootsFile = sourceRootsFile;
            this.classpath = classpath;
        }

        static Config parse(String[] args) {
            Path root = null;
            Path output = null;
            Path filesFile = null;
            Path sourceRootsFile = null;
            String classpath = null;
            for (int idx = 0; idx < args.length; idx++) {
                String arg = args[idx];
                if ("--root".equals(arg) && idx + 1 < args.length) {
                    root = Paths.get(args[++idx]).toAbsolutePath().normalize();
                } else if ("--output".equals(arg) && idx + 1 < args.length) {
                    output = Paths.get(args[++idx]).toAbsolutePath().normalize();
                } else if ("--files-file".equals(arg) && idx + 1 < args.length) {
                    filesFile = Paths.get(args[++idx]).toAbsolutePath().normalize();
                } else if ("--source-roots-file".equals(arg) && idx + 1 < args.length) {
                    sourceRootsFile = Paths.get(args[++idx]).toAbsolutePath().normalize();
                } else if ("--classpath".equals(arg) && idx + 1 < args.length) {
                    classpath = args[++idx];
                }
            }
            if (root == null || output == null || filesFile == null || sourceRootsFile == null) {
                throw new IllegalArgumentException("Missing required arguments.");
            }
            return new Config(root, output, filesFile, sourceRootsFile, classpath);
        }
    }

    private static final class GraphScanner extends TreePathScanner<Void, Void> {
        private final Trees trees;
        private final Elements elements;
        private final CompilationUnitTree unit;
        private final String relPath;
        private final PrintWriter out;
        private final Deque<String> callableStack = new ArrayDeque<>();
        private final Set<String> emittedSymbols = new TreeSet<>();
        private String packageName = "";

        GraphScanner(Trees trees, Elements elements, CompilationUnitTree unit, String relPath, PrintWriter out) {
            this.trees = trees;
            this.elements = elements;
            this.unit = unit;
            this.relPath = relPath;
            this.out = out;
        }

        @Override
        public Void visitCompilationUnit(CompilationUnitTree node, Void unused) {
            if (node.getPackageName() != null) {
                packageName = node.getPackageName().toString();
            }
            for (ImportTree importTree : node.getImports()) {
                emitRelation("imports", "file:" + relPath, importTree.getQualifiedIdentifier().toString(), false);
            }
            return super.visitCompilationUnit(node, unused);
        }

        @Override
        public Void visitClass(ClassTree node, Void unused) {
            Element element = trees.getElement(getCurrentPath());
            String symbolName = element instanceof TypeElement ? ((TypeElement) element).getQualifiedName().toString() : fallbackClassName(node);
            String owner = ownerName(element);
            emitSymbol(node.getKind().name().toLowerCase(Locale.ROOT), symbolName, node.getSimpleName().toString(), owner, isTestContext(symbolName));

            if (element instanceof TypeElement typeElement) {
                TypeElement superType = resolveType(node.getExtendsClause());
                if (superType != null && !"java.lang.Object".equals(superType.getQualifiedName().toString())) {
                    emitRelation("depends_on", symbolName, superType.getQualifiedName().toString(), true);
                }
                for (Tree impl : node.getImplementsClause()) {
                    TypeElement interfaceType = resolveType(impl);
                    if (interfaceType != null) {
                        emitRelation("implements", symbolName, interfaceType.getQualifiedName().toString(), true);
                    }
                }
                for (Tree permits : node.getPermitsClause()) {
                    TypeElement permittedType = resolveType(permits);
                    if (permittedType != null) {
                        emitRelation("depends_on", symbolName, permittedType.getQualifiedName().toString(), true);
                    }
                }
            }
            return super.visitClass(node, unused);
        }

        @Override
        public Void visitMethod(MethodTree node, Void unused) {
            Element element = trees.getElement(getCurrentPath());
            if (!(element instanceof ExecutableElement executableElement)) {
                return super.visitMethod(node, unused);
            }
            String symbolName = methodSymbolName(executableElement);
            String owner = symbolName(executableElement.getEnclosingElement());
            boolean isTest = isTestContext(symbolName);
            emitSymbol(executableElement.getKind() == ElementKind.CONSTRUCTOR ? "constructor" : "method", symbolName, node.getName().toString(), owner, isTest);
            callableStack.push(symbolName);
            try {
                return super.visitMethod(node, unused);
            } finally {
                callableStack.pop();
            }
        }

        @Override
        public Void visitMethodInvocation(MethodInvocationTree node, Void unused) {
            emitCall(node);
            return super.visitMethodInvocation(node, unused);
        }

        @Override
        public Void visitNewClass(NewClassTree node, Void unused) {
            emitCall(node);
            return super.visitNewClass(node, unused);
        }

        private void emitCall(Tree node) {
            if (callableStack.isEmpty()) {
                return;
            }
            Element element = trees.getElement(getCurrentPath());
            String target = "";
            boolean resolved = false;
            if (element instanceof ExecutableElement executableElement) {
                target = methodSymbolName(executableElement);
                resolved = true;
            } else {
                target = node.toString();
            }
            emitRelation("calls", callableStack.peek(), target, resolved);
        }

        private TypeElement resolveType(Tree tree) {
            if (tree == null) {
                return null;
            }
            Element element = trees.getElement(new TreePath(getCurrentPath(), tree));
            if (element instanceof TypeElement typeElement) {
                return typeElement;
            }
            return null;
        }

        private String fallbackClassName(ClassTree node) {
            if (packageName == null || packageName.isBlank()) {
                return node.getSimpleName().toString();
            }
            return packageName + "." + node.getSimpleName();
        }

        private String ownerName(Element element) {
            if (element == null) {
                return packageName;
            }
            Element enclosing = element.getEnclosingElement();
            if (enclosing instanceof PackageElement packageElement) {
                return packageElement.getQualifiedName().toString();
            }
            try {
                return symbolName(enclosing);
            } catch (RuntimeException ignored) {
                return packageName;
            }
        }

        private boolean isTestContext(String symbolName) {
            return relPath.contains("/src/test/java/") || relPath.startsWith("src/test/java/") || symbolName.contains("#test");
        }

        private void emitSymbol(String symbolKind, String name, String simpleName, String owner, boolean isTest) {
            if (!emittedSymbols.add(name)) {
                return;
            }
            long line = 0;
            if (getCurrentPath() != null && getCurrentPath().getLeaf() != null) {
                long position = trees.getSourcePositions().getStartPosition(unit, getCurrentPath().getLeaf());
                if (position >= 0 && unit.getLineMap() != null) {
                    line = unit.getLineMap().getLineNumber(position);
                }
            }
            out.println(
                String.join(
                    "\t",
                    "SYMBOL",
                    sanitize(symbolKind),
                    sanitize(name),
                    sanitize(simpleName),
                    sanitize(relPath),
                    Long.toString(line),
                    sanitize(owner),
                    sanitize(packageName),
                    isTest ? "1" : "0"
                )
            );
        }

        private void emitRelation(String edgeKind, String src, String dst, boolean resolved) {
            out.println(
                String.join(
                    "\t",
                    "REL",
                    sanitize(edgeKind),
                    sanitize(src),
                    sanitize(dst),
                    sanitize(relPath),
                    resolved ? "1" : "0"
                )
            );
        }
    }
}
