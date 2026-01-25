/* eslint-disable @typescript-eslint/no-explicit-any */
import { Button } from "@/components/ui/button";
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
  FieldLegend,
  FieldSet,
} from "@/components/ui/field";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useState } from "react";

const resons = [
  {
    value: "spam",
    label: "Spam",
  },
  {
    value: "inappropriate",
    label: "Inapproprié",
  },
  {
    value: "harassment",
    label: "Harcèment",
  },
  {
    value: "violence",
    label: "Violence",
  },
  {
    value: "false_info",
    label: "Information fausse",
  },
  {
    value: "other",
    label: "Autre",
  },
];

const PostReportForm = ({
  onSubmit,
  onCancel,
}: {
  onSubmit: (data: any) => void;
  onCancel?: () => void;
}) => {
  const [data, setData] = useState({
    reason: resons[0].value,
    comment: "",
  });

  const handleSubmit = (data: any) => {
    onSubmit(data);
  };

  return (
    <FieldGroup>
      <FieldSet>
        <FieldLegend>Signalement</FieldLegend>
        <FieldDescription>
          Signalez ce contenu. Nos modérateurs vérifieront sa conformité aux
          règles de la communauté dans les plus brefs délais
        </FieldDescription>
        <FieldGroup>
          <Field>
            <FieldLabel>Raison</FieldLabel>
            <Select
              value={data.reason}
              onValueChange={(value) => {
                setData({ ...data, reason: value });
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Raison" />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  {resons.map((reason) => (
                    <SelectItem key={reason.value} value={reason.value}>
                      {reason.label}
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>
          </Field>
          <Field>
            <FieldLabel>Commentaire</FieldLabel>
            <Textarea
              placeholder="Commentaire"
              onChange={(e) => {
                setData({ ...data, comment: e.target.value });
              }}
            />
          </Field>
        </FieldGroup>
      </FieldSet>
      <Field orientation={"horizontal"} className="flex justify-between">
        <Button variant={"outline"} onClick={onCancel}>
          Annuler
        </Button>
        <Button onClick={() => handleSubmit(data)}>Signaler</Button>
      </Field>
    </FieldGroup>
  );
};

export default PostReportForm;
