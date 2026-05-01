package com.priya.neurosyncdemo;

import javafx.application.Application;
import javafx.application.Platform;
import javafx.stage.Stage;
import com.priya.neurosyncdemo.ui.AuthView;
import com.priya.neurosyncdemo.ui.CoursesView;
import com.priya.neurosyncdemo.ui.Dashboard;

public class App extends Application {
    public static Stage primary;
    public static String currentUserId;
    public static String currentUserName;

    @Override
    public void start(Stage stage) {
        primary = stage;
        stage.setTitle("NeuroSync");
        stage.setMaximized(true);
        gotoLogin();
        stage.show();


        stage.setOnCloseRequest(e -> {
            try {
                // Use the static helper on Dashboard which will stop any active camera safely.
                Dashboard.stopActiveCamera();
            } catch (Exception ignored) {}
            Platform.exit();
            System.exit(0);
        });
    }

    public static void gotoLogin()   { AuthView.show(); }
    public static void gotoCourses() { CoursesView.show(); }

    public static void main(String[] args) { launch(args); }
}
