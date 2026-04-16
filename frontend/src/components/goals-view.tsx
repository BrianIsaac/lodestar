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
import type { SavingsGoal } from "@/lib/types";

interface Props {
  customerId: string;
}

export function GoalsView({ customerId }: Props) {
  const [goals, setGoals] = useState<SavingsGoal[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const list = await fetchGoals(customerId);
      setGoals(list);
    } catch {
      setGoals([]);
    } finally {
      setLoading(false);
    }
  }, [customerId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <div className="flex flex-col gap-5">
      <section className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold tracking-tight">Mục tiêu tiết kiệm</h2>
          <NewGoalDialog customerId={customerId} onCreated={refresh} />
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
              <EmptyTitle>Chưa có mục tiêu</EmptyTitle>
              <EmptyDescription>
                Tạo một mục tiêu tiết kiệm để Coach giúp bạn theo dõi tiến độ.
              </EmptyDescription>
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
          <h2 className="text-sm font-semibold tracking-tight">Mô phỏng kịch bản</h2>
          <p className="text-xs text-muted-foreground">
            Lodestar phân tích tác động trên cả bốn đơn vị Shinhan.
          </p>
        </div>
        <ScenarioSimulator customerId={customerId} />
      </section>
    </div>
  );
}

function GoalCard({ goal }: { goal: SavingsGoal }) {
  const pct =
    goal.target_amount > 0
      ? Math.min(100, Math.max(0, (goal.current_amount / goal.target_amount) * 100))
      : 0;
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">{goal.name}</CardTitle>
        <CardDescription className="text-xs">
          Hạn: {formatDate(goal.target_date)}
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
}: {
  customerId: string;
  onCreated: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [amount, setAmount] = useState("");
  const [date, setDate] = useState("");
  const [saving, setSaving] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!name || !amount || !date) return;
    setSaving(true);
    try {
      await createGoal(customerId, name, Number(amount), date);
      toast.success("Đã tạo mục tiêu mới");
      setOpen(false);
      setName("");
      setAmount("");
      setDate("");
      onCreated();
    } catch {
      toast.error("Không tạo được mục tiêu. Thử lại sau.");
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
            Tạo mục tiêu
          </Button>
        }
      />
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Mục tiêu mới</DialogTitle>
          <DialogDescription>Đặt mục tiêu tiết kiệm và theo dõi tiến độ.</DialogDescription>
        </DialogHeader>
        <form onSubmit={submit}>
          <FieldGroup>
            <Field>
              <FieldLabel htmlFor="goal-name">Tên mục tiêu</FieldLabel>
              <Input
                id="goal-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Ví dụ: Quỹ khẩn cấp"
              />
            </Field>
            <Field>
              <FieldLabel htmlFor="goal-amount">Số tiền mục tiêu (VND)</FieldLabel>
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
              <FieldLabel htmlFor="goal-date">Ngày hoàn thành</FieldLabel>
              <Input
                id="goal-date"
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
              />
            </Field>
          </FieldGroup>
          <DialogFooter className="mt-4">
            <DialogClose render={<Button variant="ghost" type="button">Huỷ</Button>} />
            <Button type="submit" disabled={saving}>
              {saving ? "Đang lưu…" : "Lưu mục tiêu"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
