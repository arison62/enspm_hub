import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";

const RichTextExpandable = ({ content }: { content: string }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showButton, setShowButton] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);

  const MAX_HEIGHT = 300; // La hauteur en pixels à partir de laquelle on coupe

  useEffect(() => {
    if (contentRef.current) {
      // On vérifie si la hauteur réelle du contenu est supérieure à notre limite
      const hasOverflow = contentRef.current.scrollHeight > MAX_HEIGHT;
      setShowButton(hasOverflow);
    }
  }, [content]); // Se déclenche quand le contenu change

  return (
    <div className="relative">
      <div
        ref={contentRef}
        style={{ maxHeight: isExpanded ? "none" : `${MAX_HEIGHT}px` }}
        className={`mt-3 prose max-w-none object-contain prose-img:mx-auto prose-img:block
          prose-img:rounded-xl 
          transition-all duration-500 overflow-hidden ${
          !isExpanded && showButton
            ? "mask-image-linear"
            : ""
        }`}
        dangerouslySetInnerHTML={{ __html: content }}
      />

      {showButton && (
        <div className="mt-2">
          <Button
            variant="link"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-0 h-auto font-bold text-blue-600"
          >
            {isExpanded ? "Voir moins" : "Voir plus"}
          </Button>
        </div>
      )}
    </div>
  );
};

export default RichTextExpandable;
