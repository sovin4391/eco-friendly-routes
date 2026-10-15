import React, { useState, useEffect, useRef } from "react";
import { Camera, AlertTriangle, ShieldCheck, Upload, Sparkles, RefreshCw, Eye, CheckCircle2, Image as ImageIcon, BarChart3 } from "lucide-react";
import { fetchRoadDamageStatus, detectRoadDamage, fetchRoadDamageSamples, fetchSampleImageBlob } from "../services/api";

const CLASS_COLORS = {
  D00: { border: "#38bdf8", bg: "rgba(56, 189, 248, 0.15)", text: "#7dd3fc", name: "Longitudinal Crack" },
  D10: { border: "#facc15", bg: "rgba(250, 204, 21, 0.15)", text: "#fde047", name: "Transverse Crack" },
  D20: { border: "#fb923c", bg: "rgba(251, 146, 60, 0.15)", text: "#fdba74", name: "Alligator Crack" },
  D40: { border: "#f43f5e", bg: "rgba(244, 63, 94, 0.2)", text: "#fda4af", name: "Pothole" },
};

export default function RoadDamageCard() {
  const [modelStatus, setModelStatus] = useState(null);
  const [loadingStatus, setLoadingStatus] = useState(true);
  const [samples, setSamples] = useState([]);
  const [loadingSamples, setLoadingSamples] = useState(false);
  const [selectedSampleFilename, setSelectedSampleFilename] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [detectionResult, setDetectionResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const canvasRef = useRef(null);
  const imageRef = useRef(null);

  useEffect(() => {
    loadStatus();
    loadSamples();
  }, []);

  async function loadStatus() {
    setLoadingStatus(true);
    const res = await fetchRoadDamageStatus();
    if (res.success) {
      setModelStatus(res.data);
    } else {
      setModelStatus({ model_loaded: false, status_message: res.error });
    }
    setLoadingStatus(false);
  }

  async function loadSamples() {
    setLoadingSamples(true);
    const res = await fetchRoadDamageSamples();
    if (res.success && res.samples.length > 0) {
      setSamples(res.samples);
    }
    setLoadingSamples(false);
  }

  function handleFileSelect(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    processSelectedFile(file);
  }

  function processSelectedFile(file, sampleName = null) {
    if (!file.type.startsWith("image/")) {
      setErrorMessage("Please select a valid JPEG or PNG image.");
      return;
    }

    setErrorMessage(null);
    setSelectedFile(file);
    setSelectedSampleFilename(sampleName);
    setDetectionResult(null);

    const reader = new FileReader();
    reader.onload = () => setPreviewUrl(reader.result);
    reader.readAsDataURL(file);
  }

  async function handleLoadSample(sample) {
    setErrorMessage(null);
    setDetectionResult(null);
    const res = await fetchSampleImageBlob(sample.url);
    if (res.success && res.blob) {
      const file = new File([res.blob], sample.filename, { type: "image/jpeg" });
      processSelectedFile(file, sample.filename);
    } else {
      setErrorMessage("Could not load sample image from backend.");
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      processSelectedFile(file);
    }
  };

  async function handleAnalyze() {
    if (!selectedFile) return;

    setIsAnalyzing(true);
    setErrorMessage(null);

    const res = await detectRoadDamage(selectedFile, 0.25);
    setIsAnalyzing(false);

    if (res.success) {
      setDetectionResult(res.data);
    } else {
      setErrorMessage(res.error || "Inference failed or model unavailable.");
    }
  }


  // Draw bounding boxes on canvas over preview image
  useEffect(() => {
    if (!detectionResult || !canvasRef.current || !imageRef.current) return;

    const img = imageRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");

    // Match canvas coordinate system to rendered image dimensions
    canvas.width = img.clientWidth;
    canvas.height = img.clientHeight;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const scaleX = img.clientWidth / (detectionResult.image_dimensions?.width || img.naturalWidth || 1);
    const scaleY = img.clientHeight / (detectionResult.image_dimensions?.height || img.naturalHeight || 1);

    (detectionResult.detections || []).forEach((det) => {
      const code = det.class_code;
      const colorInfo = CLASS_COLORS[code] || { border: "#10b981", bg: "rgba(16, 185, 129, 0.2)", text: "#6ee7b7" };

      const [xmin, ymin, xmax, ymax] = det.bbox_pixels;
      const bx = xmin * scaleX;
      const by = ymin * scaleY;
      const bw = (xmax - xmin) * scaleX;
      const bh = (ymax - ymin) * scaleY;

      // Box outline
      ctx.strokeStyle = colorInfo.border;
      ctx.lineWidth = 2.5;
      ctx.fillStyle = colorInfo.bg;
      ctx.fillRect(bx, by, bw, bh);
      ctx.strokeRect(bx, by, bw, bh);

      // Label banner
      const label = `${code} (${det.class_name}) ${(det.confidence * 100).toFixed(0)}%`;
      ctx.font = "bold 11px sans-serif";
      const textWidth = ctx.measureText(label).width;
      ctx.fillStyle = colorInfo.border;
      ctx.fillRect(bx, Math.max(0, by - 18), textWidth + 8, 18);

      ctx.fillStyle = "#0f172a";
      ctx.fillText(label, bx + 4, Math.max(12, by - 5));
    });
  }, [detectionResult, previewUrl]);

  return (
    <div id="vision" className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800/80">
        <div>
          <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Camera className="w-4 h-4 text-rose-400" />
            Module C: Road Damage & Pothole Vision Analysis
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            RDD2022 Deep Learning Pavement Quality & Surface Defect Inspection (India Split)
          </p>
        </div>

        <div className="flex items-center gap-2">
          {loadingStatus ? (
            <span className="text-[11px] px-2.5 py-1 rounded-full bg-slate-800 text-slate-400 border border-slate-700 animate-pulse">
              Checking Model...
            </span>
          ) : modelStatus?.model_loaded ? (
            <span className="text-[11px] px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              YOLOv8n Active (5-Epoch Run)
            </span>
          ) : (
            <span className="text-[11px] px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1 font-medium">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
              Standby / Demo Ready
            </span>
          )}
        </div>
      </div>

      {/* Verified Model Evaluation Metrics Banner (Phase 3 Requirement) */}
      <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 space-y-2">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-rose-400" />
            <span className="text-xs font-bold text-slate-200">
              Verified Model Evaluation Metrics (Held-Out RDD2022 India Test Split)
            </span>
          </div>
          <span className="text-[10px] text-slate-400 font-mono">
            Checkpoint: models/road_damage/best.pt
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 text-center">
          <div className="bg-slate-900/80 border border-slate-800/80 rounded-lg p-2">
            <div className="text-base font-black text-rose-400">13.01%</div>
            <div className="text-[10px] text-slate-400">mAP@0.5 (Baseline: 3.12%)</div>
          </div>
          <div className="bg-slate-900/80 border border-slate-800/80 rounded-lg p-2">
            <div className="text-base font-black text-amber-400">5.40%</div>
            <div className="text-[10px] text-slate-400">mAP@0.5:0.95 (Baseline: 0.95%)</div>
          </div>
          <div className="bg-slate-900/80 border border-slate-800/80 rounded-lg p-2">
            <div className="text-base font-black text-cyan-400">19.65%</div>
            <div className="text-[10px] text-slate-400">Precision</div>
          </div>
          <div className="bg-slate-900/80 border border-slate-800/80 rounded-lg p-2">
            <div className="text-base font-black text-emerald-400">16.39%</div>
            <div className="text-[10px] text-slate-400">Recall</div>
          </div>
        </div>

        <p className="text-[11px] text-slate-400 pt-1 leading-relaxed">
          <span className="text-slate-300 font-medium">Evaluation Disclosure:</span> Evaluated strictly against the held-out RDD2022 India test split. Class D20 (Alligator Crack) achieved 14.01% AP50 and D40 (Pothole) 5.29% AP50. Class D10 (Transverse Crack) has extreme sparsity in the test partition (10 annotations, 0.00% AP50). In accordance with capstone guidelines, this CV module serves as an experimental pavement quality inspection tool.
        </p>
      </div>

      {/* 1-Click Test Samples Selector */}
      {samples.length > 0 && (
        <div className="bg-slate-950/50 border border-slate-800/80 rounded-xl p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-xs text-slate-300 font-semibold shrink-0">
            <ImageIcon className="w-3.5 h-3.5 text-emerald-400" />
            <span>1-Click Test Samples:</span>
          </div>

          <div className="flex flex-wrap gap-2">
            {samples.map((s, idx) => (
              <button
                key={s.filename}
                type="button"
                onClick={() => handleLoadSample(s)}
                className={`text-[11px] px-3 py-1.5 rounded-lg border font-medium transition cursor-pointer flex items-center gap-1.5 ${
                  selectedSampleFilename === s.filename
                    ? "bg-rose-500/20 border-rose-500/50 text-rose-300 shadow-sm"
                    : "bg-slate-800 hover:bg-slate-750 border-slate-700 text-slate-300 hover:text-white"
                }`}
              >
                <span>Sample {idx + 1}: {s.filename}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Main Analysis Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left Column: Image Upload & Preview Area */}
        <div className="lg:col-span-7 space-y-3">
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`relative border-2 border-dashed rounded-xl bg-slate-950/60 p-4 transition-all min-h-[260px] flex flex-col items-center justify-center overflow-hidden ${
              isDragging
                ? "border-emerald-500 bg-emerald-950/20 shadow-lg shadow-emerald-950/50"
                : "border-slate-700 hover:border-slate-600"
            }`}
          >
            {previewUrl ? (
              <div className="relative w-full max-h-[380px] flex items-center justify-center">
                <img
                  ref={imageRef}
                  src={previewUrl}
                  alt="Road surface preview"
                  className="max-h-[380px] w-auto max-w-full rounded-lg object-contain shadow-lg"
                  onLoad={() => {
                    // Trigger canvas redraw on load
                    if (detectionResult) setDetectionResult({ ...detectionResult });
                  }}
                />
                <canvas
                  ref={canvasRef}
                  className="absolute top-0 left-0 w-full h-full pointer-events-none rounded-lg"
                />
              </div>
            ) : (
              <div className="text-center py-8 space-y-3">
                <div className="w-12 h-12 rounded-full bg-slate-800/80 border border-slate-700 flex items-center justify-center mx-auto text-slate-400">
                  <Upload className="w-6 h-6 text-slate-400" />
                </div>
                <div>
                  <p className="text-xs font-medium text-slate-200">
                    Drag and drop road photo here, or select from computer
                  </p>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    Supports JPEG, PNG photos from road surveys or dashcams
                  </p>
                </div>
                <label className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold cursor-pointer shadow-md transition-colors">
                  <Upload className="w-3.5 h-3.5" />
                  Select Road Photo
                  <input
                    type="file"
                    accept="image/jpeg,image/png"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                </label>
              </div>
            )}
          </div>


          {/* Action Bar */}
          {previewUrl && (
            <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
              <label className="text-xs text-slate-400 hover:text-slate-200 cursor-pointer flex items-center gap-1.5">
                <RefreshCw className="w-3.5 h-3.5" />
                Choose Different Image
                <input
                  type="file"
                  accept="image/jpeg,image/png"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </label>

              <button
                type="button"
                onClick={handleAnalyze}
                disabled={isAnalyzing || !modelStatus?.model_loaded}
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-rose-600 to-amber-600 hover:from-rose-500 hover:to-amber-500 disabled:opacity-50 text-white text-xs font-bold shadow-lg flex items-center gap-2 transition-all cursor-pointer"
              >
                {isAnalyzing ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    Analyzing Pavement...
                  </>
                ) : (
                  <>
                    <Eye className="w-3.5 h-3.5" />
                    Run Road Damage Detection
                  </>
                )}
              </button>
            </div>
          )}

          {errorMessage && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400 mt-0.5" />
              <span>{errorMessage}</span>
            </div>
          )}
        </div>

        {/* Right Column: Damage Summary & Classes */}
        <div className="lg:col-span-5 space-y-3">
          {detectionResult ? (
            <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                  Detection Summary
                </span>
                <span className={`text-[11px] px-2.5 py-0.5 rounded-full font-bold border ${
                  detectionResult.total_detections === 0
                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                    : detectionResult.damage_counts?.D40 > 0
                    ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                    : "bg-amber-500/10 text-amber-400 border-amber-500/30"
                }`}>
                  {detectionResult.pavement_status}
                </span>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 gap-2 text-center">
                <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-2.5">
                  <div className="text-xl font-black text-white">
                    {detectionResult.total_detections}
                  </div>
                  <div className="text-[10px] text-slate-400 uppercase tracking-wider mt-0.5">
                    Defects Detected
                  </div>
                </div>

                <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-2.5">
                  <div className="text-xl font-black text-amber-400">
                    {detectionResult.damage_severity_score}
                  </div>
                  <div className="text-[10px] text-slate-400 uppercase tracking-wider mt-0.5">
                    Severity Score
                  </div>
                </div>
              </div>

              {/* Category Breakdown */}
              <div className="space-y-1.5 pt-1">
                <div className="text-[11px] text-slate-400 font-medium">Defect Class Breakdown:</div>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(CLASS_COLORS).map(([code, meta]) => {
                    const count = detectionResult.damage_counts?.[code] || 0;
                    return (
                      <div
                        key={code}
                        className="bg-slate-900/60 border border-slate-800/80 rounded-lg p-2 flex items-center justify-between"
                      >
                        <div className="flex items-center gap-1.5 text-xs">
                          <span
                            className="w-2.5 h-2.5 rounded-full shrink-0"
                            style={{ backgroundColor: meta.border }}
                          />
                          <span className="text-slate-300 font-semibold">{code}</span>
                        </div>
                        <span className={`text-xs font-bold ${count > 0 ? "text-white" : "text-slate-600"}`}>
                          {count}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Individual Detections List */}
              {detectionResult.detections?.length > 0 && (
                <div className="space-y-1 pt-1 max-h-32 overflow-y-auto">
                  <div className="text-[10px] uppercase tracking-wider text-slate-500 font-semibold">
                    Individual Instances
                  </div>
                  {detectionResult.detections.map((d, i) => (
                    <div
                      key={i}
                      className="text-[11px] flex items-center justify-between py-1 px-2 rounded bg-slate-900/40 border border-slate-800/50"
                    >
                      <span className="text-slate-300 font-medium">
                        {d.class_code} · {d.class_name}
                      </span>
                      <span className="text-emerald-400 font-mono font-semibold">
                        {(d.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 space-y-3">
              <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Recognized Defect Classes
              </span>

              <div className="space-y-2">
                {Object.entries(CLASS_COLORS).map(([code, meta]) => (
                  <div
                    key={code}
                    className="bg-slate-900/60 border border-slate-800/80 rounded-lg p-2.5 flex items-center justify-between"
                  >
                    <div className="flex items-center gap-2">
                      <span
                        className="w-3 h-3 rounded-full shrink-0"
                        style={{ backgroundColor: meta.border }}
                      />
                      <div>
                        <div className="text-xs font-bold text-slate-200">
                          {code} : {meta.name}
                        </div>
                        <div className="text-[10px] text-slate-500">
                          {code === "D40" ? "Severe braking & puncture hazard" : code === "D20" ? "Structural fatigue roughness" : "Pavement surface stress"}
                        </div>
                      </div>
                    </div>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 font-mono font-medium">
                      Weight: {code === "D40" ? "3.0" : code === "D20" ? "2.0" : "1.0"}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Research & Safety Safeguard Notice */}
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 text-slate-400 text-[11px] leading-relaxed flex items-start gap-2">
            <Sparkles className="w-3.5 h-3.5 text-rose-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-slate-300">Modular Road Quality Safeguard:</span> Detected surface distress is reported strictly as local visual evidence. In accordance with project safeguards, image detections do not automatically alter baseline route distance or tailpipe CO₂ without verified geospatial segment survey telemetry.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
