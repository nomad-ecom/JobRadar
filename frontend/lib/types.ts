export type User = { id: string; email: string; name: string };

export type Profile = {
  desired_title: string;
  summary: string;
  skills: string[];
  experience_years: number | null;
  locations: string[];
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string;
  cv_path: string;
  updated_at: string | null;
};

export type Preference = {
  min_score: number;
  frequency: "instant" | "daily" | "weekly";
  sources: string[];
  email_enabled: boolean;
  last_digest_at: string | null;
};

export type Job = {
  id: string;
  source: string;
  title: string;
  company: string;
  location: string;
  salary_text: string;
  salary_min: number | null;
  salary_max: number | null;
  description: string;
  url: string;
  skills: string[];
  crawled_at: string;
};

export type Match = {
  id: string;
  score: number;
  status: "new" | "viewed" | "saved" | "applied";
  breakdown: {
    reasons?: string[];
    matched_skills?: string[];
    skills?: number;
    experience?: number;
    title?: number;
    location?: number;
    salary?: number;
  };
  notified_at: string | null;
  created_at: string;
  job: Job;
};

export type Stats = {
  total: number;
  high: number;
  new: number;
  saved: number;
  applied: number;
  notified: number;
  opened_notifications: number;
};

export type CrawlRun = {
  id: string;
  source: string;
  status: string;
  jobs_found: number;
  jobs_new: number;
  message: string;
  started_at: string;
  finished_at: string;
};

export type Notice = {
  id: string;
  subject: string;
  body: string;
  status: string;
  created_at: string;
  opened_at: string | null;
};
