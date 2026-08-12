import { useCallback, useRef, useState } from "react";
import { Upload, FileSpreadsheet, X, AlertCircle } from "lucide-react";

interface FileDropzoneProps {
  onFile: (file: File) => void;
  accept?: string;
  maxMB?: number;
  disabled?: boolean;
  currentFile?: File | null;
  onClear?: () => void;
}

const ACCEPTED = ".xlsx,.xls,.csv";
const MAX_MB_DEFAULT = 50;

export function FileDropzone({
  onFile,
  accept = ACCEPTED,
  maxMB = MAX_MB_DEFAULT,
  disabled = false,
  currentFile,
  onClear,
}: FileDropzoneProps) {
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validate = useCallback(
    (file: File): boolean => {
      setError(null);
      const ext = "." + file.name.split(".").pop()?.toLowerCase();
      const allowed = accept.split(",");
      if (!allowed.includes(ext)) {
        setError(`File type "${ext}" not supported. Use: ${accept}`);
        return false;
      }
      if (file.size > maxMB * 1024 * 1024) {
        setError(`File too large. Maximum: ${maxMB}MB`);
        return false;
      }
      return true;
    },
    [accept, maxMB]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      if (disabled) return;
      const file = e.dataTransfer.files[0];
      if (file && validate(file)) onFile(file);
    },
    [disabled, validate, onFile]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file && validate(file)) onFile(file);
      e.target.value = "";
    },
    [validate, onFile]
  );

  if (currentFile) {
    return (
      <div className="flex items-center gap-3 rounded-xl border-2 border-green-300 bg-green-50 px-5 py-4">
        <FileSpreadsheet className="w-8 h-8 text-green-600 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-green-800 truncate">{currentFile.name}</p>
          <p className="text-xs text-green-600">
            {(currentFile.size / 1024 / 1024).toFixed(2)} MB — ready to upload
          </p>
        </div>
        {onClear && (
          <button
            onClick={onClear}
            className="p-1 rounded-full hover:bg-green-100 text-green-700 transition"
            aria-label="Remove file"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div
        onDragOver={(e) => { e.preventDefault(); if (!disabled) setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => !disabled && inputRef.current?.click()}
        className={`relative flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed px-6 py-10 cursor-pointer transition-colors
          ${disabled ? "border-muted bg-muted/20 cursor-not-allowed" : ""}
          ${dragOver ? "border-[#003087] bg-[#003087]/5" : "border-border hover:border-[#003087]/50 hover:bg-muted/30"}
        `}
      >
        <div className={`w-12 h-12 rounded-full flex items-center justify-center transition-colors
          ${dragOver ? "bg-[#003087]/10" : "bg-muted"}`}>
          <Upload className={`w-6 h-6 ${dragOver ? "text-[#003087]" : "text-muted-foreground"}`} />
        </div>
        <div className="text-center">
          <p className="text-sm font-medium text-foreground">
            {dragOver ? "Drop your file here" : "Drag & drop your file here"}
          </p>
          <p className="text-xs text-muted-foreground mt-1">
            or <span className="text-[#003087] underline">browse to select</span>
          </p>
          <p className="text-xs text-muted-foreground mt-2">
            Supports: {accept} · Max {maxMB}MB
          </p>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          onChange={handleChange}
          className="hidden"
          disabled={disabled}
        />
      </div>
      {error && (
        <div className="flex items-center gap-2 text-sm text-destructive">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}
    </div>
  );
}
