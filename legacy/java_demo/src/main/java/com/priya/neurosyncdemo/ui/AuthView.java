package com.priya.neurosyncdemo.ui;

import com.priya.neurosyncdemo.App;
import com.priya.neurosyncdemo.store.UserStore;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.Scene;
import javafx.scene.control.*;
import javafx.scene.layout.*;

public class AuthView {

    public static void show() {
        var root = new BorderPane();
        root.getStyleClass().add("app");
        root.setPadding(new Insets(14));

        // Top bar: just the brand (no search on auth screen)
        var title = new Label("NeuroSync");
        title.getStyleClass().add("app-title");
        var bar = new HBox(12, title);
        bar.setAlignment(Pos.CENTER_LEFT);
        bar.getStyleClass().add("app-bar");
        root.setTop(bar);

        // Tabs: Login | Sign up (bigger, colorful via CSS)
        var tabs = new TabPane();
        tabs.getStyleClass().add("elevated-tabs");
        tabs.setTabClosingPolicy(TabPane.TabClosingPolicy.UNAVAILABLE);

        // ---- Login ----
        var loginName = new TextField(); loginName.setPromptText("Full name");
        var loginStudent = new TextField(); loginStudent.setPromptText("Student ID / Roll No");
        var loginEmail = new TextField(); loginEmail.setPromptText("Email");
        var loginPass = new PasswordField(); loginPass.setPromptText("Password");

        var loginBtn = new Button("Sign in");
        loginBtn.getStyleClass().addAll("btn","btn-primary");
        loginBtn.setOnAction(e -> {
            try {
                var us = new UserStore();
                boolean ok = false;
                String uid = null;
                if (!loginStudent.getText().isBlank()) {
                    ok = us.authenticateByStudentId(loginStudent.getText().trim(), loginPass.getText());
                    uid = loginStudent.getText().trim();
                } else if (!loginEmail.getText().isBlank()) {
                    ok = us.authenticateByEmail(loginEmail.getText().trim(), loginPass.getText());
                    // if logging by email, map to id for session/enrollment
                    uid = us.findIdByEmail(loginEmail.getText().trim());
                    if (uid == null) uid = loginEmail.getText().trim();
                }
                if (!ok) { new Alert(Alert.AlertType.ERROR, "Invalid credentials.").showAndWait(); return; }

                // ensure user row exists (prevents FK errors later)
                us.ensureUserExists(uid, loginName.getText().isBlank()? uid : loginName.getText().trim());

                App.currentUserId = uid;
                App.currentUserName = loginName.getText().isBlank()? uid : loginName.getText().trim();
                App.gotoCourses();
            } catch (Exception ex) {
                new Alert(Alert.AlertType.ERROR, ex.getMessage()).showAndWait();
            }
        });

        var loginForm = new VBox(12, new Label("Welcome! Sign in to continue."),
                loginName, loginStudent, loginEmail, loginPass, loginBtn);
        loginForm.setPadding(new Insets(20));
        loginForm.getStyleClass().add("card");
        loginForm.setPrefWidth(640);
        loginForm.setPrefHeight(300);              // taller
        var loginWrap = new VBox(loginForm);
        loginWrap.setAlignment(Pos.CENTER);
        loginWrap.setPadding(new Insets(32,0,0,0));
        var loginTab = new Tab("Login", loginWrap);

        // ---- Sign up ----
        var sName = new TextField(); sName.setPromptText("Full name");
        var sStudent = new TextField(); sStudent.setPromptText("Student ID / Roll No");
        var sEmail = new TextField(); sEmail.setPromptText("Email ID");
        var sPass = new PasswordField(); sPass.setPromptText("Password (min 6 chars)");

        var signupBtn = new Button("Create account"); signupBtn.getStyleClass().addAll("btn","btn-accent");
        signupBtn.setOnAction(e -> {
            try {
                new UserStore().signUp(sName.getText().trim(), sEmail.getText().trim(),
                        sStudent.getText().trim(), sPass.getText());
                new Alert(Alert.AlertType.INFORMATION, "Account created. You can log in now.").showAndWait();
                tabs.getSelectionModel().select(0);
            } catch (Exception ex) {
                new Alert(Alert.AlertType.ERROR, ex.getMessage()).showAndWait();
            }
        });

        var signupForm = new VBox(12, new Label("Create your NeuroSync account."),
                sName, sStudent, sEmail, sPass, signupBtn);
        signupForm.setPadding(new Insets(20));
        signupForm.getStyleClass().add("card");
        signupForm.setPrefWidth(640);
        signupForm.setPrefHeight(300);
        var signupWrap = new VBox(signupForm);
        signupWrap.setAlignment(Pos.CENTER);
        signupWrap.setPadding(new Insets(32,0,0,0));
        var signupTab = new Tab("Sign up", signupWrap);

        tabs.getTabs().addAll(loginTab, signupTab);
        root.setCenter(tabs);

        var scene = new Scene(root, 1280, 800);
        scene.getStylesheets().add(AuthView.class.getResource("/styles/neurosync.css").toExternalForm());
        App.primary.setScene(scene);
        App.primary.setMaximized(true);
    }
}
