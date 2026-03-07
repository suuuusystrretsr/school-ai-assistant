export type ExplanationMode = 'eli5' | 'normal' | 'advanced' | 'teacher';

export interface DashboardMetric {
  label: string;
  value: string;
  delta: string;
}
