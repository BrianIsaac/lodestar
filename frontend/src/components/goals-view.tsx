"use client";

import { useCallback, useEffect, useState } from "react";
import { Plus, Target } from "lucide-react";
import { toast } from "sonner";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field";
import { ScenarioSimulator } from "@/components/scenario-simulator";
import { createGoal, fetchGoals } from "@/lib/api";
import { formatDate, formatVND } from "@/lib/format";
import { useT } from "@/lib/i18n";
import type { SavingsGoal } from "@/lib/types";

interface Props {
  customerId: string;
  /** Optional preset coming from a feed card quick-prompt (?goal_*). When
   *  present the dialog opens on mount with the values pre-filled. */
  goalPreset?: {
    name?: string;
    amount?: string;
    months?: string;
  };
}

export function GoalsView({ customerId, goalPreset }: Props) {
  const [goals, setGoals] = useState<SavingsGoal[]>([]);
  const [loading, setLoading] = useState(true);
  const { t } = useT();

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const list = await fetchGoals(customerId);
      setGoals(list);
    } catch {
      toast.error(t("goals_fetch_error"));
      setGoals([]);
    } finally {
      setLoading(false);
    }
  }, [customerId, t]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <div className="flex flex-col gap-5">
      <section className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold tracking-tight">{t("goals_heading")}</h2>
          <NewGoalDialog customerId={customerId} onCreated={refresh} preset={goalPreset} />
        </div>

        {loading ? (
          <div className="flex flex-col gap-3">
            {Array.from({ length: 2 }).map((_, i) => (
              <Skeleton key={i} className="h-24 w-full rounded-xl" />
            ))}
          </div>
        ) : goals.length === 0 ? (
          <Empty>
            <EmptyHeader>
              <EmptyMedia variant="icon">
                <Target />
              </EmptyMedia>
              <EmptyTitle>{t("goals_empty_title")}</EmptyTitle>
              <EmptyDescription>{t("goals_empty_desc")}</EmptyDescription>
            </EmptyHeader>
          </Empty>
        ) : (
          <div className="flex flex-col gap-3">
            {goals.map((g) => (
              <GoalCard key={g.goal_id} goal={g} />
            ))}
          </div>
        )}
      </section>

      <section className="flex flex-col gap-3">
        <div>
          <h2 className="text-sm font-semibold tracking-tight">{t("sim_heading")}</h2>
          <p className="text-xs text-muted-foreground">{t("sim_subheading")}</p>
        </div>
        <ScenarioSimulator customerId={customerId} />
      </section>
    </div>
  );
}

function GoalCard({ goal }: { goal: SavingsGoal }) {
  const { t } = useT();
  const pct =
    goal.target_amount > 0
      ? Math.min(100, Math.max(0, (goal.current_amount / goal.target_amount) * 100))
      : 0;
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">{goal.name}</CardTitle>
        <CardDescription className="text-xs">
          {t("goals_deadline")}: {formatDate(goal.target_date)}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-2">
        <Progress value={pct} />
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">
            {formatVND(goal.current_amount)} / {formatVND(goal.target_amount)}
          </span>
          <span className="font-semibold text-primary">{pct.toFixed(0)}%</span>
        </div>
      </CardContent>
    </Card>
  );
}

function NewGoalDialog({
  customerId,
  onCreated,
  preset,
}: {
  customerId: string;
  onCreated: () => void;
  preset?: { name?: string; amount?: string; months?: string };
}) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [amount, setAmount] = useState("");
  const [date, setDate] = useState("");
  const [saving, setSaving] = useState(false);
  const { t } = useT();

  // When a feed quick-prompt deep-links in (?goal_name=…), pre-fill and
  // open the dialog. Runs only once per preset snapshot.
  useEffect(() => {
    if (!preset?.name) return;
    setName(preset.name);
    if (preset.amount) setAmount(preset.amount);
    if (preset.months) {
      const months = Number(preset.months);
      if (!Number.isNaN(months) && months > 0) {
        const target = new Date();
        target.setMonth(target.getMonth() + months);
        setDate(target.toISOString().slice(0, 10));
      }
    }
    setOpen(true);
  }, [preset?.name, preset?.amount, preset?.months]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!name || !amount || !date) return;
    setSaving(true);
    try {
      await createGoal(customerId, name, Number(amount), date);
      toast.success(t("goals_created"));
      setOpen(false);
      setName("");
      setAmount("");
      setDate("");
      onCreated();
    } catch {
      toast.error(t("goals_create_error"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger
        render={
          <Button size="sm" variant="secondary">
            <Plus data-icon="inline-start" />
            {t("goals_new")}
          </Button>
        }
      />
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("goals_dialog_title")}</DialogTitle>
          <DialogDescription>{t("goals_dialog_desc")}</DialogDescription>
        </DialogHeader>
        <form onSubmit={submit}>
          <FieldGroup>
            <Field>
              <FieldLabel htmlFor="goal-name">{t("goals_field_name")}</FieldLabel>
              <Input
                id="goal-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder={t("goals_field_name_placeholder")}
              />
            </Field>
            <Field>
              <FieldLabel htmlFor="goal-amount">{t("goals_field_amount")}</FieldLabel>
              <Input
                id="goal-amount"
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="50000000"
                min={0}
              />
            </Field>
            <Field>
              <FieldLabel htmlFor="goal-date">{t("goals_field_date")}</FieldLabel>
              <Input
                id="goal-date"
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
              />
            </Field>
          </FieldGroup>
          <DialogFooter className="mt-4">
            <DialogClose
              render={
                <Button variant="ghost" type="button">
                  {t("goals_cancel")}
                </Button>
              }
            />
            <Button type="submit" disabled={saving}>
              {saving ? t("goals_saving") : t("goals_save")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
