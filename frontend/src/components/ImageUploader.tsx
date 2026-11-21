import React, { useRef, useState } from 'react';
import {
  UploadCloud,
  Image as ImageIcon,
  CheckCircle2,
  AlertCircle,
  X,
  RefreshCw,
  Sparkles,
  Camera,
  ShieldAlert,
} from 'lucide-react';

interface ImageUploaderProps {
  onAnalyze: (file: File) => void;
  isLoading: boolean;
}

export const ImageUploader: React.FC<ImageUploaderProps> = ({ onAnalyze, isLoading }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [clientError, setClientError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateAndSetFile = (file: File) => {
    setClientError(null);
    const validTypes = ['image/jpeg', 'image/png', 'image/jpg'];
    if (!validTypes.includes(file.type.toLowerCase())) {
      setClientError('Unsupported format. Please upload a clear JPG, JPEG, or PNG photograph.');
      return;
    }

    if (file.size > 20 * 1024 * 1024) {
      setClientError('File exceeds 20MB. Please select a smaller photo.');
      return;
    }

    setSelectedFile(file);
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleClear = () => {
    setSelectedFile(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
    setClientError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleAnalyzeClick = () => {
    if (selectedFile && !isLoading) {
      onAnalyze(selectedFile);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="max-w-3xl w-full mx-auto space-y-6 sm:space-y-8">
      {/* Header Section */}
      <div className="text-center px-2">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-teal-50 border border-teal-200/80 text-teal-800 text-[11px] sm:text-xs font-semibold uppercase tracking-wider mb-2 sm:mb-3">
          <Camera className="w-3.5 h-3.5" />
          Skin Lesion Screening
        </div>
        <h1 className="text-2xl sm:text-3xl md:text-4xl font-extrabold text-slate-900 tracking-tight mb-2 sm:mb-3">
          Skin Lesion Analysis
        </h1>
        <p className="text-sm sm:text-base text-slate-600 max-w-xl mx-auto leading-relaxed">
          Upload a clear image of a skin lesion to receive an AI-assisted screening assessment.
        </p>
      </div>

      {/* Main Upload Box */}
      <div className="bg-white rounded-2xl sm:rounded-3xl border border-slate-200/90 shadow-md shadow-slate-200/50 p-4 sm:p-6 md:p-8 transition-all">
        <input
          ref={fileInputRef}
          type="file"
          accept="image/png, image/jpeg, image/jpg"
          className="hidden"
          onChange={handleFileChange}
        />

        {!selectedFile ? (
          /* Empty Drag & Drop Area */
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onClick={() => fileInputRef.current?.click()}
            className={`cursor-pointer rounded-xl sm:rounded-2xl border-2 border-dashed p-6 sm:p-10 md:p-14 text-center transition-all flex flex-col items-center justify-center ${
              isDragOver
                ? 'border-teal-500 bg-teal-50/50 scale-[1.005]'
                : 'border-slate-300 hover:border-teal-400 hover:bg-slate-50/70 bg-slate-50/30'
            }`}
          >
            <div className="w-12 h-12 sm:w-16 sm:h-16 rounded-2xl bg-teal-50 text-teal-700 flex items-center justify-center mb-3 sm:mb-5 shadow-xs">
              <UploadCloud className="w-6 h-6 sm:w-8 sm:h-8" />
            </div>
            <h3 className="text-base sm:text-lg font-bold text-slate-800 mb-1 px-2">
              Drag & drop your skin lesion image here
            </h3>
            <p className="text-xs sm:text-sm text-slate-500 mb-4 sm:mb-5">
              or <span className="text-teal-700 font-semibold underline underline-offset-2">browse files</span> from your device
            </p>
            <div className="flex flex-wrap items-center justify-center gap-1.5 sm:gap-2 text-[11px] sm:text-xs text-slate-400 font-medium">
              <span className="px-2 py-0.5 bg-white border border-slate-200 rounded">JPG</span>
              <span className="px-2 py-0.5 bg-white border border-slate-200 rounded">JPEG</span>
              <span className="px-2 py-0.5 bg-white border border-slate-200 rounded">PNG</span>
              <span className="text-slate-400">• Max 20MB</span>
            </div>
          </div>
        ) : (
          /* Selected File Preview Area */
          <div className="space-y-4 sm:space-y-6">
            <div className="relative rounded-xl sm:rounded-2xl overflow-hidden border border-slate-200 bg-slate-900/5 flex items-center justify-center min-h-[200px] max-h-[300px] sm:max-h-[380px]">
              <img
                src={previewUrl!}
                alt="Uploaded skin lesion"
                className="max-h-[300px] sm:max-h-[380px] w-auto max-w-full object-contain rounded-xl"
              />
              <button
                onClick={handleClear}
                disabled={isLoading}
                className="absolute top-2.5 right-2.5 sm:top-3 sm:right-3 p-2 bg-slate-900/70 hover:bg-slate-900 text-white rounded-full backdrop-blur-xs transition-colors disabled:opacity-50 min-h-[36px] min-w-[36px] flex items-center justify-center cursor-pointer"
                title="Remove image"
                aria-label="Remove image"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* File Info Card */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 sm:p-4 rounded-xl bg-slate-50 border border-slate-200">
              <div className="flex items-center gap-3 overflow-hidden">
                <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-lg bg-teal-100/70 text-teal-800 flex items-center justify-center shrink-0">
                  <ImageIcon className="w-5 h-5" />
                </div>
                <div className="truncate min-w-0 flex-1">
                  <div className="text-xs sm:text-sm font-bold text-slate-800 truncate">{selectedFile.name}</div>
                  <div className="text-[11px] sm:text-xs text-slate-500">{formatFileSize(selectedFile.size)}</div>
                </div>
              </div>
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={isLoading}
                className="text-xs font-bold text-teal-700 hover:text-teal-900 px-3 py-1.5 rounded-lg hover:bg-teal-50 border sm:border-transparent border-teal-200 transition-colors disabled:opacity-50 shrink-0 self-end sm:self-center min-h-[36px] flex items-center justify-center cursor-pointer"
              >
                Change Photo
              </button>
            </div>
          </div>
        )}

        {/* Error Alert */}
        {clientError && (
          <div className="mt-4 p-3 sm:p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
            <span className="leading-relaxed">{clientError}</span>
          </div>
        )}

        {/* Action Button */}
        <div className="mt-5 sm:mt-6">
          <button
            onClick={handleAnalyzeClick}
            disabled={!selectedFile || isLoading}
            className={`w-full py-3.5 sm:py-4 px-4 sm:px-6 rounded-xl sm:rounded-2xl font-bold text-sm sm:text-base flex items-center justify-center gap-2.5 transition-all shadow-md min-h-[48px] ${
              !selectedFile || isLoading
                ? 'bg-slate-200 text-slate-400 cursor-not-allowed shadow-none'
                : 'bg-teal-700 hover:bg-teal-800 text-white shadow-teal-700/25 active:scale-[0.99] cursor-pointer'
            }`}
          >
            {isLoading ? (
              <>
                <RefreshCw className="w-4 h-4 sm:w-5 sm:h-5 animate-spin" />
                <span>Running Screening Pipeline...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 sm:w-5 sm:h-5" />
                <span>Analyze Image</span>
              </>
            )}
          </button>
        </div>

        {/* Loading Progress Info */}
        {isLoading && (
          <div className="mt-4 p-3.5 sm:p-4 rounded-xl bg-teal-50/70 border border-teal-100 text-xs text-teal-900 space-y-2 animate-pulse">
            <div className="font-semibold text-teal-800">Processing in progress:</div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-1.5 sm:gap-2 text-[11px] text-teal-700">
              <div>• 1. Image focus & skin gate</div>
              <div>• 2. ResNet18 + Texture extraction</div>
              <div>• 3. Grad-CAM visual attention</div>
            </div>
          </div>
        )}
      </div>

      {/* Guidelines Box */}
      <div className="bg-white/80 rounded-xl sm:rounded-2xl border border-slate-200/80 p-4 sm:p-5 text-xs text-slate-600">
        <div className="font-bold text-slate-800 mb-2 flex items-center gap-1.5">
          <CheckCircle2 className="w-4 h-4 text-teal-600 shrink-0" />
          <span>Guidelines for Best Screening Accuracy:</span>
        </div>
        <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2 pl-4 list-disc text-slate-600 leading-relaxed">
          <li>Take a direct, close-up photograph of the single lesion or mark.</li>
          <li>Ensure good lighting without harsh shadows or strong glare.</li>
          <li>Make sure the camera is focused on the lesion (avoid blur).</li>
          <li>Avoid portraits, full-body images, documents, or unrelated objects.</li>
        </ul>
        <div className="mt-3 pt-3 border-t border-slate-100 flex items-start sm:items-center gap-2 text-slate-500 text-[11px]">
          <ShieldAlert className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5 sm:mt-0" />
          <span>Educational screening prototype. Never replaces direct in-person evaluation by a board-certified dermatologist.</span>
        </div>
      </div>
    </div>
  );
};
