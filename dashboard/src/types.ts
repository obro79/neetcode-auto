export type Confidence = "struggling" | "getting_there" | "solid";
export type ReviewStage = "new" | "1d" | "3d" | "7d" | "14d" | "30d" | "mastered";
export type DailySlot = "review" | "focused_new" | "random_new" | "done";
export type Difficulty = "easy" | "medium" | "hard";

export interface DashboardConfig {
  apiBaseUrl: string;
  apiKey: string;
}

export interface ProgressOut {
  solved: boolean;
  review_stage: ReviewStage;
  next_review: string | null;
  last_practiced: string | null;
  confidence: Confidence | null;
  daily_slot: DailySlot | null;
}

export interface ProblemWithProgress {
  id: number;
  slug: string;
  title: string;
  pattern: string;
  difficulty: Difficulty;
  leetcode_url: string;
  neetcode_url: string;
  sort_order: number;
  progress: ProgressOut | null;
}

export interface ConfidenceBreakdown {
  struggling: number;
  getting_there: number;
  solid: number;
  unset: number;
}

export interface PatternStat {
  pattern: string;
  solved: number;
  total: number;
}

export interface StatsSummary {
  total: number;
  solved: number;
  unsolved: number;
  by_confidence: ConfidenceBreakdown;
  by_review_stage: Record<ReviewStage, number>;
  by_pattern: PatternStat[];
  due_today: number;
  due_overdue: number;
  mastered: number;
}

export interface DailySetItem {
  slug: string;
  title: string;
  pattern: string;
  difficulty: Difficulty;
  leetcode_url: string;
  neetcode_url: string;
  slot: DailySlot;
  completed: boolean;
}

export interface DailySet {
  set_date: string;
  focus_pattern: string | null;
  review: DailySetItem[];
  focused_new: DailySetItem[];
  random_new: DailySetItem[];
}
