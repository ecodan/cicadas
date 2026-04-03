package com.acme;

public class Calculator {
    public int add(int left, int right) {
        return CalculatorHelper.normalize(left + right);
    }
}
