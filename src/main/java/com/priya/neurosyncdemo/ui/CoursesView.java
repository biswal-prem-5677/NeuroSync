package com.priya.neurosyncdemo.ui;

import com.priya.neurosyncdemo.App;
import com.priya.neurosyncdemo.service.PointsService;
import com.priya.neurosyncdemo.store.CourseStore;
import com.priya.neurosyncdemo.store.EnrollmentStore;
import com.priya.neurosyncdemo.store.UserStore;
import javafx.animation.TranslateTransition;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.Scene;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.layout.*;
import javafx.util.Duration;

import java.util.List;

public class CoursesView {

    public static void show() {
        var root = new BorderPane();
        root.getStyleClass().add("app");
        root.setPadding(new Insets(14));

        // Top bar: title + spacer + points + avatar
        var title = new Label("Courses"); title.getStyleClass().add("app-title");
        var spacer = new Region(); HBox.setHgrow(spacer, Priority.ALWAYS);

        var points = new Label();
        points.getStyleClass().add("points-badge");
        try { points.setText("⭐ " + new PointsService().balance(App.currentUserId)); }
        catch (Exception ignored) { points.setText("⭐ 0"); }

        var avatar = avatarButton(App.currentUserName);
        var bar = new HBox(12, title, spacer, points, avatar);
        bar.setAlignment(Pos.CENTER_LEFT);
        bar.getStyleClass().add("app-bar");
        root.setTop(bar);

        // Right drawer (account panel)
        var drawer = accountDrawer();
        BorderPane.setAlignment(drawer, Pos.TOP_RIGHT);
        root.setRight(drawer);
        avatar.setOnAction(e -> toggleDrawer(drawer));

        // Grid of course tiles
        var grid = new FlowPane(18,18);
        grid.setPrefWrapLength(1200);
        grid.setPadding(new Insets(8));

        List<String[]> seed = List.of(
                new String[]{"cse101", "Programming Fundamentals"},
                new String[]{"mat201", "Discrete Mathematics"},
                new String[]{"phy110", "Physics Essentials"},
                new String[]{"ml301",  "Intro to Machine Learning"}
        );
        var cs = new CourseStore();
        for (var c: seed) {
            try { cs.upsert(c[0], c[1]); } catch (Exception ignored) {}
            grid.getChildren().add(courseTile(c[0], c[1]));
        }

        var centerCard = new VBox(grid);
        centerCard.getStyleClass().add("card");
        centerCard.setPadding(new Insets(16));
        root.setCenter(centerCard);

        var scene = new Scene(root, 1600, 900);
        scene.getStylesheets().add(CoursesView.class.getResource("/styles/neurosync.css").toExternalForm());
        App.primary.setScene(scene);
        App.primary.setMaximized(true);
    }

    private static Button avatarButton(String name) {
        String initials = "?";
        if (name != null && !name.isBlank()) {
            var parts = name.trim().split("\\s+");
            initials = ("" + parts[0].charAt(0) + (parts.length>1?parts[1].charAt(0):' ')).trim().toUpperCase();
        }
        var b = new Button(initials);
        b.getStyleClass().addAll("btn");
        b.setPrefSize(44,44);
        return b;
    }

    private static StackPane accountDrawer() {
        var who = new Label(App.currentUserName + " (" + App.currentUserId + ")");
        var signOut = new Button("Sign out"); signOut.getStyleClass().addAll("btn","btn-danger");
        signOut.setOnAction(e -> { App.currentUserId=null; App.currentUserName=null; App.gotoLogin(); });

        var v = new VBox(12, new Label("Account"), who, signOut);
        v.getStyleClass().add("right-drawer");
        v.setPrefWidth(280);
        v.setTranslateX(320); // hidden offscreen initially
        return new StackPane(v);
    }

    private static void toggleDrawer(StackPane drawer) {
        var pane = (Region)drawer.getChildren().get(0);
        double target = pane.getTranslateX() > 0 ? 0 : 320;
        var tt = new TranslateTransition(Duration.millis(220), pane);
        tt.setToX(target);
        tt.play();
    }

    private static StackPane courseTile(String id, String title) {
        var label = new Label(title); label.getStyleClass().add("tile-title");

        var tile = new VBox(8, label);
        tile.getStyleClass().add("course-tile");
        tile.setPrefSize(280, 120);
        tile.setOnMouseClicked(e -> {
            try {
                new UserStore().ensureUserExists(App.currentUserId, App.currentUserName); // avoid FK fail
                new EnrollmentStore().enroll(App.currentUserId, id);
            } catch (Exception ignored) {}
            Dashboard.openForCourse(id, title);
        });

        var wrap = new StackPane(tile);
        wrap.getStyleClass().add("tile-wrap");
        return wrap;
    }
}
