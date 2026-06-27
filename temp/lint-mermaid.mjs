import fs from "node:fs";
import mermaid from "mermaid";

const text = fs.readFileSync("temp/core-flows.md", "utf8");
const blocks = [...text.matchAll(/```mermaid\n([\s\S]*?)```/g)].map((match) => match[1]);

for (let index = 0; index < blocks.length; index += 1) {
  try {
    await mermaid.parse(blocks[index]);
    console.log(`block ${index + 1}: OK`);
  } catch (error) {
    console.log(`block ${index + 1}: ERROR`);
    console.log(error.str || error.message || error);
  }
}
