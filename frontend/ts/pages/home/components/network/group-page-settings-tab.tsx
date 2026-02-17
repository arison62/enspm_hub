import { useGroupActions } from "@/api/network/groups";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Globe, Trash2, Lock } from "lucide-react";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import type { GroupOut } from "@/types/network";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useEffect } from "react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { toast } from "sonner";
import { router } from "@inertiajs/react";

interface Props {
  groupe: GroupOut;
  form: {
    nom: string;
    description: string;
    type_acces: "public" | "prive";
    status: "actif" | "inactif";
    est_ferme: boolean;
    image_base64: string;
  };
  setForm: React.Dispatch<
    React.SetStateAction<{
      nom: string;
      description: string;
      type_acces: "public" | "prive";
      status: "actif" | "inactif";
      est_ferme: boolean;
      image_base64: string;
    }>
  >;
}

export default function GroupPageSettingsTab({
  groupe: { id },
  form,
  setForm,
}: Props) {
  const { updateGroup, deleteGroup } = useGroupActions();
  useEffect(() => {
    const update = async () => {
      await updateGroup.mutateAsync({ id, data: form });
    };
    update();
  }, [form]);
  const handleDelete = async () => {
    await deleteGroup.mutateAsync(id, {
      onError: (error) => {
        console.log(error);
        toast.error(error.message);
      },
      onSuccess: () => {
        toast.success("Groupe supprimé");
        router.visit("/network");
      },
    });
  };
  return (
    <div className="max-w-2xl">
      <Card>
        <CardHeader>
          <CardTitle>Paramètres du groupe</CardTitle>
          <CardDescription>
            Modifiez les paramètres avancés du groupe
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <Label>Visibilité du groupe</Label>
                <Select
                  value={form.type_acces}
                  onValueChange={(value) => {
                    setForm((prev) => ({
                      ...prev,
                      type_acces: value === "public" ? "public" : "prive",
                    }));
                  }}
                >
                  <SelectTrigger>
                    <SelectValue className="text-sm" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="public">
                      <Globe className="mr-2 h-4 w-4" />
                      Public
                    </SelectItem>
                    <SelectItem value="prive">
                      <Lock className="mr-2 h-4 w-4" />
                      Privé
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Fermer le groupe</Label>
                <p className="text-sm text-muted-foreground">
                  Seuls les admins pourront publier du contenu
                </p>
              </div>
              <Switch
                checked={form.est_ferme}
                onCheckedChange={(checked) =>
                  setForm((prev) => ({
                    ...prev,
                    est_ferme: checked,
                  }))
                }
              />
            </div>
            <Separator />
            <div className="pt-4">
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="destructive" className="w-full sm:w-auto">
                    <Trash2 className="h-4 w-4 mr-2" />
                    Supprimer le groupe
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent size="sm">
                  <AlertDialogHeader>
                    <AlertDialogTitle>
                      Êtes-vous sûr de vouloir supprimer le groupe ?
                    </AlertDialogTitle>
                    <AlertDialogDescription>
                      Cette action est irréversible.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Annuler</AlertDialogCancel>
                    <AlertDialogAction onClick={handleDelete}>
                      Supprimer
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
