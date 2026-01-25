import { useEffect, useState } from "react";
import RichTextEditor from "@/components/rich-text-editor/feeds/rich-text-editor";
import { usePostAction } from "@/api/feeds";
import { toast } from "sonner";
import { useInternalNav } from "@/contexts/internal-nav-context";

const MAX_SIZE_MB = 10;
const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024;

const isContentTooLarge = (content: string) => {
  const sizeInBytes = new Blob([content]).size;
  return sizeInBytes > MAX_SIZE_BYTES;
};

const FormCreatePost = () => {
  const { pop } = useInternalNav();

  const { createPost } = usePostAction();
  const { mutate, isSuccess, isError, isPending } = createPost;
  const [canSubmit, setCanSubmit] = useState(false);
  const [content, setContent] = useState("");

  const handleContentChange = (value: string) => {
    setContent(value);

    if (value.trim().length > 0 && !isContentTooLarge(value)) {
      setCanSubmit(true);
    } else {
      setCanSubmit(false);
    }
    if (isContentTooLarge(value)) {
      toast.error("Contenu trop long");
    }
  };
  const handleSubmit = () => {
    mutate(content);
  };
  useEffect(() => {
    if (isSuccess) {
      setContent("");
      setCanSubmit(false);
      toast.success("Post cree avec success");
      pop();
    }
    if (isError) {
      toast.error("Une erreur est survenue");
    }
  }, [isError, isSuccess, pop]);
  return (
    <div>
      <RichTextEditor
        onChange={handleContentChange}
        canSubmit={canSubmit}
        placeholder="Quoi de neuf ?"
        isLoading={isPending}
        onCancel={() => {}}
        onSubmit={handleSubmit}
      />
    </div>
  );
};

export default FormCreatePost;
