package com.priya.neurosyncdemo.ui;

public class LoginView {
    public static void show() {
        AuthView.show(); // single source of truth for Login/Signup
    }
}
