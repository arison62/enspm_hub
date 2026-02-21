import React, {
  createContext,
  useContext,
  useRef,
  useState,
  useEffect,
} from "react";
import { Paperclip, X, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn, convertFileToBase64 } from "@/lib/utils";

// ============================================
// TYPES & CONTEXT
// ============================================

interface FileInputContextValue {
  loading: boolean;
  progress: number;
  hasFile: boolean;
  previewBase64: string | null;
  previewFile: File | null;
  handleClick: () => void;
  handleDelete: () => void;
  inputRef: React.RefObject<HTMLInputElement | null>;
  handleFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

const FileInputContext = createContext<FileInputContextValue | null>(null);

const useFileInput = () => {
  const context = useContext(FileInputContext);
  if (!context) {
    throw new Error("FileInput components must be used within <FileInput>");
  }
  return context;
};

// ============================================
// ROOT COMPONENT
// ============================================

interface FileInputProps {
  onError(error: string): void;
  onFileLoaded(base64: string, file: File): void;
  onProgress(progress: number): void;
  onCancel(): void;
  onDelete(): void;
  hasFile?: boolean;
  previewBase64?: string | null;
  previewFile?: File | null;
  children: React.ReactNode;
}

export const FileInput: React.FC<FileInputProps> & {
  Trigger: typeof FileInputTrigger;
  Preview: typeof FileInputPreview;
} = ({
  onError,
  onFileLoaded,
  onProgress,
  onCancel,
  onDelete,
  hasFile: externalHasFile = false,
  previewBase64: externalBase64 = null,
  previewFile: externalFile = null,
  children,
}) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);

  // État interne pour le mode non-contrôlé
  const [internalBase64, setInternalBase64] = useState<string | null>(null);
  const [internalFile, setInternalFile] = useState<File | null>(null);

  // Déterminer si on est en mode contrôlé ou non
  const isControlled = externalHasFile || externalBase64 !== null;

  // Utiliser les valeurs externes si fournies, sinon l'état interne
  const previewBase64 = isControlled ? externalBase64 : internalBase64;
  const previewFile = isControlled ? externalFile : internalFile;
  const fileExists = isControlled
    ? externalHasFile
    : !!(internalBase64 || externalBase64);

  // SYNCHRONISATION: Réinitialiser l'état interne quand l'externe change
  useEffect(() => {
    if (!externalHasFile && !externalBase64) {
      setInternalBase64(null);
      setInternalFile(null);
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    }
  }, [externalHasFile, externalBase64]);

  const MAX_FILE_SIZE_MB = 15;

  const simulateProgress = () => {
    setProgress(0);
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 90) {
          clearInterval(interval);
          return prev;
        }
        return prev + 10;
      });
    }, 100);
    return interval;
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (fileExists) {
      onError("Veuillez d'abord supprimer le fichier actuel.");
      return;
    }

    if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      onError(
        `Le fichier dépasse la taille maximale de ${MAX_FILE_SIZE_MB} Mo.`,
      );
      return;
    }

    setLoading(true);
    const progressInterval = simulateProgress();
    onProgress(0);

    try {
      const base64 = await convertFileToBase64(file, MAX_FILE_SIZE_MB);

      clearInterval(progressInterval);
      setProgress(100);
      onProgress(100);

      // Mettre à jour l'état interne seulement si non contrôlé
      if (!isControlled) {
        setInternalBase64(base64);
        setInternalFile(file);
      }

      onFileLoaded(base64, file);
    } catch (error) {
      clearInterval(progressInterval);
      onError(
        error instanceof Error ? error.message : "Erreur lors du chargement.",
      );
      onCancel();
    } finally {
      setLoading(false);
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    }
  };

  const handleClick = () => {
    if (fileExists) return;
    inputRef.current?.click();
  };

  const handleDelete = () => {
    // Réinitialiser l'état interne
    setInternalBase64(null);
    setInternalFile(null);
    setProgress(0);

    // Réinitialiser l'input
    if (inputRef.current) {
      inputRef.current.value = "";
    }

    // Appeler le callback externe
    onDelete();
  };

  const value: FileInputContextValue = {
    loading,
    progress,
    hasFile: fileExists,
    previewBase64,
    previewFile,
    handleClick,
    handleDelete,
    inputRef,
    handleFileSelect,
  };

  return (
    <FileInputContext.Provider value={value}>
      <input
        ref={inputRef}
        type="file"
        className="hidden"
        onChange={handleFileSelect}
        accept="image/*,application/pdf,.doc,.docx,.txt,.mp4,.mp3"
        disabled={loading}
      />
      {children}
    </FileInputContext.Provider>
  );
};

// ============================================
// TRIGGER COMPONENT
// ============================================

interface FileInputTriggerProps {
  children?: React.ReactNode;
  className?: string;
  asChild?: boolean;
}

const FileInputTrigger: React.FC<FileInputTriggerProps> = ({
  children,
  className,
  asChild = false,
}) => {
  const { loading, progress, hasFile, handleClick } = useFileInput();

  // Cercle de progression SVG
  const renderCircularProgress = () => {
    const radius = 10;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference - (progress / 100) * circumference;

    return (
      <div className="relative h-5 w-5">
        <svg className="h-full w-full -rotate-90" viewBox="0 0 24 24">
          <circle
            cx="12"
            cy="12"
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            className="text-muted-foreground/20"
          />
          <circle
            cx="12"
            cy="12"
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            className="text-primary transition-all duration-300 ease-out"
          />
        </svg>
      </div>
    );
  };

  if (asChild && children) {
    return (
      <div
        onClick={hasFile ? undefined : handleClick}
        className={cn(hasFile && "pointer-events-none opacity-50", className)}
      >
        {loading ? renderCircularProgress() : children}
      </div>
    );
  }

  return (
    <Button
      variant="ghost"
      size="icon"
      className={cn(className, "shrink-0")}
      onClick={handleClick}
      disabled={loading || hasFile}
      title={
        hasFile
          ? "Supprimez le fichier actuel pour en importer un autre"
          : "Joindre un fichier"
      }
    >
      {loading
        ? renderCircularProgress()
        : (children ?? <Paperclip className="h-5 w-5" />)}
    </Button>
  );
};

// ============================================
// PREVIEW COMPONENT
// ============================================

interface FileInputPreviewProps extends React.ComponentProps<"div"> {
  emptyState?: React.ReactNode;
}

const FileInputPreview: React.FC<FileInputPreviewProps> = ({
  className,
  emptyState,
  ...props
}) => {
  const { hasFile, previewBase64, previewFile, handleDelete } = useFileInput();

  const isImageFile = (file: File): boolean => {
    return file.type.startsWith("image/");
  };

  if (!hasFile || !previewBase64 || !previewFile) {
    return emptyState ? <>{emptyState}</> : null;
  }

  const isImage = isImageFile(previewFile);

  return (
    <div
      className={cn(
        "flex items-center gap-3 rounded-lg border bg-secondary/50 p-3",
        className,
      )}
      {...props}
    >
      {/* Miniature */}
      <div className="relative shrink-0">
        {isImage ? (
          <div className="relative h-16 w-16 overflow-hidden rounded-md border">
            <img
              src={previewBase64}
              alt={previewFile.name}
              className="h-full w-full object-cover"
            />
          </div>
        ) : (
          <div className="flex h-16 w-16 items-center justify-center rounded-md bg-muted border">
            <FileText className="h-8 w-8 text-muted-foreground" />
          </div>
        )}
      </div>

      {/* Infos */}
      <div className="flex-1 min-w-0">
        <p className="truncate text-sm font-medium">{previewFile.name}</p>
        <p className="text-xs text-muted-foreground">
          {(previewFile.size / 1024 / 1024).toFixed(2)} Mo
          {isImage && " • Image"}
        </p>
      </div>

      {/* Bouton suppression */}
      <Button
        variant="ghost"
        size="icon"
        className="shrink-0 h-8 w-8 hover:bg-destructive/10 hover:text-destructive"
        onClick={handleDelete}
        title="Supprimer pour importer un autre fichier"
      >
        <X className="h-4 w-4" />
      </Button>
    </div>
  );
};

// ============================================
// EXPORTS
// ============================================

FileInput.Trigger = FileInputTrigger;
FileInput.Preview = FileInputPreview;

export { FileInputTrigger, FileInputPreview };
