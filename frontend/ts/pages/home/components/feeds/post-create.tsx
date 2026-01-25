import { useEffect, useState } from "react";
import RichTextEditor from "@/components/rich-text-editor/feeds/rich-text-editor";
import { usePostAction } from "@/api/feeds";
import { toast } from "sonner";
import { useInternalNav } from "@/contexts/internal-nav-context";

const FormCreatePost = () => {
    const {pop} = useInternalNav();

  const { createPost } = usePostAction();
  const { mutate, isSuccess, isError, isPending} = createPost;
  const [canSubmit, setCanSubmit] = useState(false);
  const [content, setContent] = useState("");

  const handleContentChange = (value: string) => {
    setContent(value);
    const parser = new DOMParser();
    const doc = parser.parseFromString(value, "text/html");
    if (doc.body.textContent.trim().length > 0) {
      setCanSubmit(true);
    } else {
      setCanSubmit(false);
    }
  };
  const handleSubmit = () => {
    mutate(content);
  };
  useEffect(() => {
    if (isSuccess) {
      setContent("")
      setCanSubmit(false);
      toast.success("Post cree avec success");
      pop();
    }
    if (isError) {
      toast.error("Une erreur est survenue");
    }
  }, [isError, isSuccess, pop])
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
