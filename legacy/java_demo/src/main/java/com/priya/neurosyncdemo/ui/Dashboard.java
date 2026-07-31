package com.priya.neurosyncdemo.ui;

import com.priya.neurosyncdemo.App;
import com.priya.neurosyncdemo.api.EmotionAPI;
import com.priya.neurosyncdemo.api.EmotionResult;
import com.priya.neurosyncdemo.core.DecisionEngine;
import com.priya.neurosyncdemo.core.EmotionMapper;
import com.priya.neurosyncdemo.service.*;
import com.priya.neurosyncdemo.store.CourseStore;
import com.priya.neurosyncdemo.store.EnrollmentStore;
import com.priya.neurosyncdemo.store.UserStore;
import com.priya.neurosyncdemo.util.LoggerUtil;
import javafx.animation.TranslateTransition;
import javafx.application.Platform;
import javafx.collections.FXCollections;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.Scene;
import javafx.scene.chart.*;
import javafx.scene.control.*;
import javafx.scene.image.*;
import javafx.scene.layout.*;
import javafx.util.Duration;
import org.bytedeco.javacv.Java2DFrameConverter;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.nio.file.Path;
import java.time.Instant;
import java.time.ZoneId;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;

public class Dashboard extends BorderPane {

    public static void openForCourse(String courseId, String courseTitle) {
        try {
            new CourseStore().upsert(courseId, courseTitle);
            new UserStore().ensureUserExists(App.currentUserId, App.currentUserName); // FK safety
            new EnrollmentStore().enroll(App.currentUserId, courseId);
        } catch (Exception ignored) {}

        var stage = App.primary;
        var view = new Dashboard(courseId, courseTitle);
        var scene = new Scene(view, 1600, 900);
        scene.getStylesheets().add(App.class.getResource("/styles/neurosync.css").toExternalForm());
        stage.setScene(scene);
        stage.setMaximized(true);
    }

    private final String courseId;
    @SuppressWarnings("unused")
    private final String courseTitle;

    private final Label status = new Label("Ready.");
    private final Label action = new Label("");
    private final ImageView preview = new ImageView();
    private File currentFile;

    private org.bytedeco.javacv.FrameGrabber grabber;
    private Thread cameraThread;

    private final AtomicBoolean running = new AtomicBoolean(false);
    private BufferedImage lastFrameBuffered;
    private Java2DFrameConverter frameConverter;

    private ScheduledExecutorService scheduler;
    private Long currentSessionId = null;
    // --------- Single global handle so App can stop camera and monitoring on exit ---------
    private static volatile Dashboard activeInstance = null;

    /**
     * Called by App on JVM / JavaFX shutdown to stop any running camera and monitoring scheduler.
     * Safe to call multiple times.
     */
    public static void stopActiveCamera() {
        Dashboard inst = activeInstance;
        if (inst == null) return;

        // stop monitoring scheduler if active
        try {
            var sched = inst.scheduler;
            if (sched != null) {
                try { sched.shutdownNow(); } catch (Exception ignored) {}
                inst.scheduler = null;
            }
        } catch (Throwable ignored) {}

        // stop camera (calls private stopCamera() inside same class)
        try { inst.stopCamera(); } catch (Exception ignored) {}

        // clear reference
        activeInstance = null;
    }



    private final PieChart distChart = new PieChart();
    private final CategoryAxis timeAxis = new CategoryAxis();
    private final NumberAxis confAxis = new NumberAxis(0, 100, 10);
    private final LineChart<String, Number> timelineChart = new LineChart<>(timeAxis, confAxis);

    private final Map<String, ProgressBar> progressBars = new HashMap<>();
    private final Map<String, Label> progressLabels = new HashMap<>();

    private final EmotionStore emotionStore = new EmotionStore();
    private final AnalyticsService analytics = new AnalyticsService();
    private final PointsService points = new PointsService();

    public Dashboard(String courseId, String courseTitle) {
        activeInstance = this;
        this.courseId = courseId; this.courseTitle = courseTitle;

        getStyleClass().add("app");
        setPadding(new Insets(16));

        // ===== Top bar: title + points + avatar (toggles right drawer) =====
        var title = new Label("Course • " + courseTitle); title.getStyleClass().add("app-title");
        var spacer = new Region(); HBox.setHgrow(spacer, Priority.ALWAYS);

        var who = new Label(App.currentUserName + " (" + App.currentUserId + ")");
        var pts = new Label(); pts.getStyleClass().add("points-badge"); refreshPoints(pts);

        var avatar = new Button(avatarInitials(App.currentUserName));
        avatar.getStyleClass().add("btn"); avatar.setPrefSize(44,44);

        var changePwd = new Button("Change Password"); changePwd.getStyleClass().add("btn");
        changePwd.setOnAction(e -> ChangePasswordDialog.showAndUpdate());
        var back = new Button("All Courses"); back.getStyleClass().add("btn"); back.setOnAction(e -> App.gotoCourses());

        var bar = new HBox(12, title, spacer, who, pts, changePwd, back, avatar);
        bar.getStyleClass().add("app-bar");
        setTop(bar);

        // Right account drawer
        var drawer = accountDrawer();
        setRight(drawer);
        avatar.setOnAction(e -> toggleDrawer(drawer));

        // ===== Left controls & camera =====
        preview.setFitWidth(560); preview.setPreserveRatio(true);
        preview.setFitHeight(360);

        var choose = btn("Choose Image"); choose.setOnAction(e -> onChoose());
        var detectFile = btnPrimary("Detect"); detectFile.setOnAction(e -> onDetectFromFile());
        var startCam = btn("Start Camera"); startCam.setOnAction(e -> startCamera());
        var stopCam = btn("Stop Camera"); stopCam.setOnAction(e -> stopCamera());
        var snap = btnPrimary("Capture & Detect"); snap.setOnAction(e -> onCaptureAndDetect());
        var startMon = btnPrimary("Start Monitoring"); startMon.setOnAction(e -> onStartMonitoring());
        var stopMon = btnDanger("Stop Monitoring"); stopMon.setOnAction(e -> onStopMonitoring());

        var controls = new VBox(10,
                new HBox(10, choose, detectFile),
                new HBox(10, startCam, stopCam, snap),
                new HBox(10, startMon, stopMon),
                new VBox(8, status, action)
        );
        var left = new VBox(14, card("Controls", controls), card("Camera", preview));
        VBox.setVgrow(left, Priority.ALWAYS);

        // ===== Right analytics =====
        var progressPanel = buildProgressPanel();

        distChart.setTitle("Session Emotion Distribution");
        distChart.setLegendVisible(false);
        distChart.setPrefHeight(300);

        timelineChart.setTitle("Top Confidence Over Time");
        timelineChart.setCreateSymbols(true);
        timelineChart.setPrefHeight(260);

        // Right analytics pane (scrollable vertically so charts never get cut off)
        var right = new VBox(14,
                card("Session Progress", progressPanel),
                card("Distribution", distChart),
                card("Confidence", timelineChart)
        );
        right.setPadding(new Insets(8));
        right.setFillWidth(true);
        VBox.setVgrow(right, Priority.ALWAYS);

        // Wrap right column in a vertical ScrollPane so charts are reachable on small screens
        var rightScroll = new ScrollPane(right);
        rightScroll.setFitToWidth(true);
        rightScroll.setHbarPolicy(ScrollPane.ScrollBarPolicy.NEVER);
        rightScroll.setVbarPolicy(ScrollPane.ScrollBarPolicy.AS_NEEDED);
        // optional: prefer a minimum viewport height so it looks good when window is large
        rightScroll.setPrefViewportHeight(520);

        // Make center columns horizontally layout with the left controls and the scrollable right
        var columns = new HBox(20, left, rightScroll);
        columns.setPadding(new Insets(6));
        HBox.setHgrow(rightScroll, Priority.ALWAYS);
        var centerCard = card(null, columns);
        var centerScroll = new ScrollPane(centerCard);
        centerScroll.setFitToWidth(true);
        centerScroll.setHbarPolicy(ScrollPane.ScrollBarPolicy.NEVER);
        centerScroll.setVbarPolicy(ScrollPane.ScrollBarPolicy.AS_NEEDED);
        setCenter(centerScroll);


        // ---- Safe shutdown hook to ensure camera and threads are released ----
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            try {
                if (running.get()) {
                    running.set(false);
                    if (grabber != null) {
                        try { grabber.stop(); } catch (Exception ignored) {}
                        try { grabber.release(); } catch (Exception ignored) {}
                        grabber = null;
                    }
                }
                if (frameConverter != null) {
                    try { frameConverter.close(); } catch (Exception ignored) {}
                }
                if (cameraThread != null && cameraThread.isAlive()) {
                    try { cameraThread.join(200); } catch (InterruptedException ignored) {}
                }
            } catch (Exception ignored) {}
        }));



    }

    // ---- helpers UI ----
    private static String avatarInitials(String name) {
        if (name == null || name.isBlank()) return "?";
        var parts = name.trim().split("\\s+");
        return ("" + parts[0].charAt(0) + (parts.length>1?parts[1].charAt(0):' ')).trim().toUpperCase();
    }
    private Button btn(String t){ var b=new Button(t); b.getStyleClass().add("btn"); return b; }
    private Button btnPrimary(String t){ var b=new Button(t); b.getStyleClass().addAll("btn","btn-primary"); return b; }
    private Button btnDanger(String t){ var b=new Button(t); b.getStyleClass().addAll("btn","btn-danger"); return b; }
    private void refreshPoints(Label badge){ try { badge.setText("⭐ " + points.balance(App.currentUserId)); } catch (Exception ignored){ badge.setText("⭐ ?"); } }

    private StackPane card(String title, javafx.scene.Node content) {
        var box = new VBox(8);
        if (title != null && !title.isBlank()) {
            var t = new Label(title); t.getStyleClass().add("card-title");
            box.getChildren().add(t);
        }
        box.getChildren().add(content);
        var wrapper = new StackPane(box); wrapper.getStyleClass().add("card");
        return wrapper;
    }

    private StackPane accountDrawer() {
        var who = new Label(App.currentUserName + " (" + App.currentUserId + ")");
        var signOut = new Button("Sign out"); signOut.getStyleClass().addAll("btn","btn-danger");
        signOut.setOnAction(e -> { App.currentUserId=null; App.currentUserName=null; App.gotoLogin(); });

        var v = new VBox(12, new Label("Account"), who, signOut);
        v.getStyleClass().add("right-drawer");
        v.setPrefWidth(300);
        v.setTranslateX(340);
        var wrap = new StackPane(v);
        StackPane.setAlignment(v, Pos.TOP_RIGHT);
        return wrap;
    }

    private void toggleDrawer(StackPane drawer) {
        var pane = (Region)drawer.getChildren().get(0);
        double target = pane.getTranslateX() > 0 ? 0 : 340;
        var tt = new TranslateTransition(Duration.millis(220), pane);
        tt.setToX(target); tt.play();
    }

    // ---- file ----
    private void onChoose() {
        var fc = new javafx.stage.FileChooser();
        fc.getExtensionFilters().add(new javafx.stage.FileChooser.ExtensionFilter("Images","*.jpg","*.jpeg","*.png"));
        var f = fc.showOpenDialog(App.primary);
        if (f != null) { currentFile = f; status.setText("Selected: " + f.getName()); action.setText(""); preview.setImage(new Image(f.toURI().toString())); }
    }

    private void onDetectFromFile() {
        if (currentFile == null) { status.setText("No image selected."); return; }
        status.setText("Detecting (file) …");
        CompletableFuture.supplyAsync(() -> {
                    try (EmotionAPI api = new EmotionAPI(null)) { return api.detectAllEmotions(Path.of(currentFile.getAbsolutePath())); }
                    catch (Exception ex) { throw new CompletionException(ex); }
                }).thenAccept(r -> Platform.runLater(() -> handleResult(r,"file")))
                .exceptionally(ex -> { Platform.runLater(()-> status.setText("Error: "+ex.getCause().getMessage())); return null; });
    }


    // ---- camera (lower res/fps to avoid memory issues) ----
    @SuppressWarnings("resource")
    private void startCamera() {
        if (running.get()) { status.setText("Camera already running."); return; }

        Exception lastEx = null;
        org.bytedeco.javacv.FrameGrabber localGrabber = null;
        int[] deviceCandidates = new int[]{0, 1};

        for (int idx : deviceCandidates) {
            // 1) Try OpenCVFrameGrabber
            {
                org.bytedeco.javacv.OpenCVFrameGrabber g = null;
                try {
                    g = new org.bytedeco.javacv.OpenCVFrameGrabber(idx);
                    g.setImageWidth(480); g.setImageHeight(360); g.setFrameRate(10);
                    g.start();
                    localGrabber = g;
                    g = null; // prevent cleanup since ownership transferred to localGrabber
                    break;
                } catch (Exception e) {
                    lastEx = e;
                    if (g != null) { try { g.stop(); } catch (Exception ignored) {} try { g.release(); } catch (Exception ignored) {} }
                }
            }

            // 2) Try Windows VideoInputFrameGrabber (DirectShow) - safe check
            try {
                var g = org.bytedeco.javacv.VideoInputFrameGrabber.createDefault(idx);
                if (g != null) {
                    g.setImageWidth(480); g.setImageHeight(360); g.setFrameRate(10);
                    g.start();
                    localGrabber = g;
                    break;
                }
            } catch (Throwable t) { lastEx = (t instanceof Exception) ? (Exception)t : new Exception(t); }

            // 3) Try FFmpegFrameGrabber with a platform-appropriate device string
            {
                org.bytedeco.javacv.FFmpegFrameGrabber fg = null;
                try {
                    String os = System.getProperty("os.name").toLowerCase();
                    if (os.contains("win")) {
                        // Use dshow device string (commonly works on Windows)
                        fg = new org.bytedeco.javacv.FFmpegFrameGrabber("video=dshow:0");
                    } else {
                        // On Linux/macOS, attempt /dev/videoN path for idx (Linux). macOS may not work with this.
                        fg = new org.bytedeco.javacv.FFmpegFrameGrabber("/dev/video" + idx);
                    }
                    fg.setImageWidth(480); fg.setImageHeight(360); fg.setFrameRate(10);
                    fg.start();
                    localGrabber = fg;
                    fg = null; // prevent cleanup since ownership transferred to localGrabber
                    break;
                } catch (Exception e) {
                    lastEx = e;
                    if (fg != null) { try { fg.stop(); } catch (Exception ignored) {} try { fg.release(); } catch (Exception ignored) {} }
                }
            }
        }

        if (localGrabber == null) {
            String msg = "Camera open failed" + (lastEx == null ? "" : ": " + lastEx.getMessage());
            status.setText("Camera error: " + msg);
            if (lastEx != null) lastEx.printStackTrace();
            return;
        }

        // assign the generic grabber (no cast)
        grabber = localGrabber;
        running.set(true);
        frameConverter = new Java2DFrameConverter();

        cameraThread = new Thread(() -> {
            int nullFrameCounter = 0;
            while (running.get()) {
                try {
                    org.bytedeco.javacv.Frame frame = grabber.grab();
                    if (frame == null || frame.image == null) {
                        nullFrameCounter++;
                        if (nullFrameCounter > 8) {
                            final String emsg = "Cannot read frames from camera (null returned).";
                            Platform.runLater(() -> status.setText("Camera error: " + emsg));
                            break;
                        }
                        Thread.sleep(100);
                        continue;
                    }
                    nullFrameCounter = 0;
                    BufferedImage bi = frameConverter.getBufferedImage(frame);
                    if (bi == null) continue;
                    lastFrameBuffered = bi;
                    WritableImage fx = bufferedImageToWritableImage(bi);
                    Platform.runLater(() -> preview.setImage(fx));
                } catch (Exception ex) {
                    ex.printStackTrace();
                    final String msg = ex.getMessage() == null ? ex.toString() : ex.getMessage();
                    Platform.runLater(() -> status.setText("Camera read error: " + msg));
                    break;
                }
            }

            // cleanup when loop ends
            try {
                running.set(false);
                if (grabber != null) {
                    try { grabber.stop(); } catch (Exception ignored) {}
                    try { grabber.release(); } catch (Exception ignored) {}
                }
                if (frameConverter != null) frameConverter.close();
            } catch (Exception ignored) {}
        }, "camera-loop");

        cameraThread.setDaemon(true);
        cameraThread.start();
        status.setText("Camera started.");
    }




    /**
     * Public, safe stop routine — stops camera thread, grabber, scheduler, and clears session.
     * Made public so external callers (App.stop) can request a full cleanup.
     */
    public synchronized void stopCamera() {
        // Stop scheduled monitoring if running
        try {
            if (scheduler != null) {
                scheduler.shutdownNow();
                scheduler = null;
            }
        } catch (Exception ignored) {}

        // Clear current session id to avoid further DB inserts
        currentSessionId = null;

        // Signal the camera thread to stop
        running.set(false);

        // Join camera thread (short timeout)
        try {
            if (cameraThread != null) {
                cameraThread.join(500);
                cameraThread = null;
            }
        } catch (InterruptedException ignored) {}

        // Stop & release grabber safely
        try {
            if (grabber != null) {
                try { grabber.stop(); } catch (Exception ignored) {}
                try { grabber.release(); } catch (Exception ignored) {}
                grabber = null;
            }
        } catch (Exception ignored) {}

        // Dispose frame converter
        try {
            if (frameConverter != null) {
                frameConverter.close();
                frameConverter = null;
            }
        } catch (Exception ignored) {}

        // reset last frame buffer
        lastFrameBuffered = null;

        // UI updates (run on FX thread)
        try {
            Platform.runLater(() -> {
                status.setText("Camera stopped.");
                progressBars.values().forEach(b -> b.setProgress(0));
                progressLabels.forEach((e,l) -> l.setText(e + ": 0%"));
                // clear preview image to avoid holding native resources
                preview.setImage(null);
            });
        } catch (Exception ignored) {}

        // Clear static handle if this instance is the active one
        if (activeInstance == this) activeInstance = null;
    }





    private static WritableImage bufferedImageToWritableImage(BufferedImage bi) {
        if (bi == null) return null;
        int w = bi.getWidth(), h = bi.getHeight();
        WritableImage wr = new WritableImage(w, h);
        PixelWriter pw = wr.getPixelWriter();
        int[] rgb = new int[w*h];
        bi.getRGB(0,0,w,h,rgb,0,w);
        pw.setPixels(0,0,w,h, PixelFormat.getIntArgbInstance(), rgb,0,w);
        return wr;
    }

    private void onCaptureAndDetect() {
        if (lastFrameBuffered == null) { status.setText("No frame yet. Start camera."); return; }
        status.setText("Detecting (webcam) …");
        var baos = new ByteArrayOutputStream();
        try { ImageIO.write(lastFrameBuffered, "jpg", baos); } catch (Exception e) { status.setText("Error: "+e.getMessage()); return; }
        byte[] jpeg = baos.toByteArray();

        CompletableFuture.supplyAsync(() -> {
                    try (EmotionAPI api = new EmotionAPI(null)) { return api.detectAllEmotions(jpeg); }
                    catch (Exception ex) { throw new CompletionException(ex); }
                }).thenAccept(r -> Platform.runLater(() -> handleResult(r,"webcam")))
                .exceptionally(ex -> { Platform.runLater(()-> status.setText("Error: "+ex.getCause().getMessage())); return null; });
    }

    // ---- monitoring ----
    private void onStartMonitoring() {
        try {
            if (currentSessionId != null) {
                status.setText("Monitoring already active.");
                return;
            }
            if (!running.get()) {
                Platform.runLater(() -> {
                    Alert alert = new Alert(Alert.AlertType.WARNING);
                    alert.setTitle("Camera Not Started");
                    alert.setHeaderText("Start Camera First");
                    alert.setContentText("Please click 'Start Camera' before starting monitoring.");
                    alert.showAndWait();
                });
                return; // ✅ Stop here, don’t auto-start camera
            }

            // FK safety
            new UserStore().ensureUserExists(App.currentUserId, App.currentUserName);

            currentSessionId = emotionStore.createSession(App.currentUserId, courseId, System.currentTimeMillis());
            status.setText("Monitoring started.");

            scheduler = Executors.newSingleThreadScheduledExecutor();
            scheduler.scheduleAtFixedRate(() -> {
                try {
                    if (lastFrameBuffered == null || currentSessionId == null) return;
                    var baos = new ByteArrayOutputStream();
                    ImageIO.write(lastFrameBuffered, "jpg", baos);
                    EmotionResult r;
                    try (EmotionAPI api = new EmotionAPI(null)) {
                        r = api.detectAllEmotions(baos.toByteArray());
                    }
                    Platform.runLater(() -> handleResult(r, "webcam"));
                } catch (Exception ignored) {}
            }, 0, 5, TimeUnit.SECONDS);
        } catch (Exception ex) {
            status.setText("DB error: " + ex.getMessage());
        }
    }


    private void onStopMonitoring() {
        if (scheduler != null) { scheduler.shutdownNow(); scheduler = null; }
        currentSessionId = null;
        status.setText("Monitoring stopped.");
        progressBars.values().forEach(b -> b.setProgress(0));
        progressLabels.forEach((e,l) -> l.setText(e + ": 0%"));
    }

    // ---- glue ----
    private void handleResult(EmotionResult r, String source) {
        if (currentSessionId == null) {
            try { currentSessionId = emotionStore.createSession(App.currentUserId, courseId, System.currentTimeMillis()); }
            catch (Exception ex) { status.setText("DB error: " + ex.getMessage()); return; }
        }
        String derived = EmotionMapper.derivedLabel(r);
        String top = r.topEmotion();
        double conf = r.topConfidence()==null?0:r.topConfidence();
        String act = DecisionEngine.actionForDerived(derived);

        status.setText("Base: " + top + "  (" + String.format("%.1f", conf) + "%)   →  Derived: " + derived);
        action.setText("Next: " + act);
        LoggerUtil.log(System.currentTimeMillis() + "," + source + "," + top + "→" + derived + "," + act);

        try { if (Set.of("CONFIDENT","EXCITED","ANTICIPATION").contains(derived)) new PointsService().award(App.currentUserId, +1, "Positive engagement"); }
        catch (Exception ignored) {}

        try { emotionStore.insertEmotionEvent(currentSessionId, System.currentTimeMillis(), source, derived, r); refreshAnalytics(); }
        catch (Exception e) { status.setText("DB error: " + e.getMessage()); }
    }

    @SuppressWarnings("unchecked")
    private void refreshAnalytics() {
        if (currentSessionId == null) return;
        try {
            var dist = analytics.distributionForSession(currentSessionId);
            var data = FXCollections.<PieChart.Data>observableArrayList();
            int total = dist.values().stream().mapToInt(i->i).sum();
            for (var e : dist.entrySet()) data.add(new PieChart.Data(e.getKey(), e.getValue()));
            distChart.setData(data);
            updateProgressPanel(dist, total);
        } catch (Exception ignored) {}

        try {
            var map = analytics.confidenceTimeline(currentSessionId);
            XYChart.Series<String, Number> series = new XYChart.Series<>();
            series.setName("Top confidence (%)");
            for (var e : map.entrySet()) {
                String label = Instant.ofEpochMilli(e.getKey()).atZone(ZoneId.systemDefault()).toLocalTime().withNano(0).toString();
                series.getData().add(new XYChart.Data<>(label, e.getValue()));
            }
            timelineChart.getData().setAll(series);
        } catch (Exception ignored) {}
    }

    private VBox buildProgressPanel() {
        var box = new VBox(6);
        for (String e : new String[]{ "CONFIDENT","EXCITED","ANTICIPATION","SLEEPY","BORED","NERVOUS","FRUSTRATED","DOUBTFUL","DISGUST","NEUTRAL" }) {
            var l = new Label(e + ": 0%");
            var bar = new ProgressBar(0); bar.setPrefWidth(300);
            progressBars.put(e, bar); progressLabels.put(e, l);
            var row = new HBox(8, l, bar); row.setAlignment(Pos.CENTER_LEFT);
            box.getChildren().add(row);
        }
        return box;
    }

    private void updateProgressPanel(Map<String,Integer> counts, int total) {
        if (total <= 0) { progressBars.values().forEach(b -> b.setProgress(0)); progressLabels.forEach((e,l)-> l.setText(e + ": 0%")); return; }
        for (var entry : progressBars.entrySet()) {
            String e = entry.getKey(); int c = counts.getOrDefault(e, 0);
            double pct = c * 1.0 / total; entry.getValue().setProgress(pct);
            progressLabels.get(e).setText(e + String.format(": %.0f%%", pct * 100));
        }
    }

    // simple inline dialog for password change
    private static class ChangePasswordDialog {
        static void showAndUpdate() {
            var dlg = new Dialog<Void>(); dlg.setTitle("Change Password");
            var oldP = new PasswordField(); oldP.setPromptText("Current password");
            var newP = new PasswordField(); newP.setPromptText("New password");
            var ok = new ButtonType("Update", ButtonBar.ButtonData.OK_DONE);
            dlg.getDialogPane().getButtonTypes().addAll(ok, ButtonType.CANCEL);
            dlg.getDialogPane().setContent(new VBox(10, oldP, newP));
            dlg.setResultConverter(bt -> null);
            dlg.showAndWait().ifPresent(v -> {
                try {
                    new com.priya.neurosyncdemo.store.UserStore().changePassword(App.currentUserId, oldP.getText(), newP.getText());
                    new Alert(Alert.AlertType.INFORMATION, "Password updated.").showAndWait();
                } catch (Exception ex) { new Alert(Alert.AlertType.ERROR, "Error: " + ex.getMessage()).showAndWait(); }
            });
        }
    }
}
