// Precomputed benchmark metrics
// Mirrors /api/metrics/precomputed from the FastAPI backend

export const PRECOMPUTED_METRICS = {
  router: {
    total: 74,
    correct: 74,
    accuracy: 1.0,
    real_total: 59,
    real_correct: 59,
    real_accuracy: 1.0,
  },
  visual: {
    num_samples: 21,
    real_count: 16,
    synth_count: 5,
    mean_cell_accuracy: 0.884,
    mean_f1_score: 0.8431,
    exact_match_rate: 0.667,
    real_cell_accuracy: 0.847,
    real_f1: 0.7941,
    synth_cell_accuracy: 0.978,
    synth_f1: 0.971,
    per_class: [
      { label: "Traffic Light", f1: 0.82, count: 2 },
      { label: "Bus", f1: 0.75, count: 2 },
      { label: "Bicycle", f1: 0.88, count: 1 },
      { label: "Car", f1: 0.92, count: 1 },
      { label: "Crosswalk", f1: 0.80, count: 2 },
      { label: "Fire Hydrant", f1: 0.78, count: 2 },
      { label: "Motorcycle", f1: 0.83, count: 2 },
      { label: "Bridge", f1: 0.90, count: 1 },
      { label: "Stairs", f1: 0.71, count: 1 },
      { label: "Chimney", f1: 0.85, count: 2 },
    ],
  },
  audio: {
    num_samples: 25,
    real_count: 20,
    synth_count: 5,
    mean_char_accuracy: 0.296,
    mean_cer: 0.704,
    exact_match_rate: 0.20,
    real_exact_match: 0.0,
    real_cer: 1.288,
    synth_exact_match: 1.0,
    synth_cer: 0.0,
    real_samples: [
      { id: "017ddc45", expected: "71t2", cer: 1.5, lev_dist: 6 },
      { id: "1566a7ac", expected: "16h6", cer: 1.25, lev_dist: 5 },
      { id: "38a53bb4", expected: "0396", cer: 1.0, lev_dist: 4 },
      { id: "3df81dfb", expected: "4296", cer: 1.25, lev_dist: 5 },
      { id: "86a9cf98", expected: "6923", cer: 1.5, lev_dist: 6 },
      { id: "c3587b40", expected: "a3f2", cer: 1.25, lev_dist: 5 },
      { id: "cc818f15", expected: "b7x9", cer: 1.0, lev_dist: 4 },
      { id: "d76ba939", expected: "k4p2", cer: 1.5, lev_dist: 6 },
      { id: "e35618bb", expected: "m9n3", cer: 1.25, lev_dist: 5 },
      { id: "eaef535c", expected: "r7s1", cer: 1.0, lev_dist: 4 },
    ],
  },
  puzzle: {
    num_samples: 28,
    independent_real_count: 20,
    demo_count: 3,
    synth_count: 5,
    overall_accuracy: 0.4286,
    mean_pixel_error: 70.3,
    independent_real_accuracy: 0.25,
    independent_real_mean_error: 92.4,
    demo_accuracy: 0.667,
    demo_mean_error: 38.3,
    synth_accuracy: 1.0,
    synth_mean_error: 1.0,
    error_bins: [
      { range: "0–10px", count: 6 },
      { range: "11–30px", count: 4 },
      { range: "31–60px", count: 3 },
      { range: "61–100px", count: 5 },
      { range: "101–150px", count: 6 },
      { range: ">150px", count: 4 },
    ],
  },
} as const;

export type Metrics = typeof PRECOMPUTED_METRICS;

// Accuracy comparison data for the bar chart
export const ACCURACY_COMPARISON = [
  { modality: "Router", synthetic: 100, real: 100 },
  { modality: "Visual", synthetic: 97.8, real: 84.7 },
  { modality: "Audio", synthetic: 100, real: 0 },
  { modality: "Puzzle", synthetic: 100, real: 25.0 },
];

// Domain gap data for area chart
export const DOMAIN_GAP_SERIES = [
  { name: "Router", gap: 0 },
  { name: "Visual", gap: 13.1 },
  { name: "Audio", gap: 100 },
  { name: "Puzzle", gap: 75 },
];
