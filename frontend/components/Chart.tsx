"use client";

import dynamic from "next/dynamic";
import type { ResultEvent } from "@/lib/api";

// Plotly touches window, so it can only load client-side.
const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

// Apple system colors — vivid but harmonious, blue leads.
const PALETTE = [
  "#0071e3",
  "#30b0c7",
  "#34c759",
  "#ff9500",
  "#af52de",
  "#ff2d55",
  "#5856d6",
  "#64d2ff",
];

const FONT = {
  family:
    'var(--font-geist-sans), -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  color: "#1d1d1f",
  size: 13,
};

const BASE_LAYOUT = {
  paper_bgcolor: "transparent",
  plot_bgcolor: "transparent",
  font: FONT,
  margin: { l: 56, r: 16, t: 8, b: 44 },
  showlegend: false,
  xaxis: { gridcolor: "#ececed", zeroline: false, automargin: true },
  yaxis: { gridcolor: "#ececed", zeroline: false, automargin: true },
};

const CONFIG = { displayModeBar: false, responsive: true };

interface ChartProps {
  columns: string[];
  rows: Record<string, unknown>[];
  spec: NonNullable<ResultEvent["viz_spec"]>;
}

export default function Chart({ rows, spec }: ChartProps) {
  const x = spec.x;
  const y = spec.y;
  if (!x || !y) return null;

  const xs = rows.map((r) => r[x] as string | number);
  const ys = rows.map((r) => Number(r[y]));

  let data: Record<string, unknown>[];

  if (spec.chart_type === "hbar") {
    // Horizontal: categories on y, measure on x — long labels stay readable.
    data = [
      {
        x: ys,
        y: xs,
        type: "bar",
        orientation: "h",
        marker: { color: PALETTE[0] },
      },
    ];
  } else if (spec.chart_type === "scatter") {
    data = [
      {
        x: xs,
        y: ys,
        type: "scatter",
        mode: "markers",
        marker: { color: PALETTE[0], size: 8, opacity: 0.7 },
      },
    ];
  } else if (spec.chart_type === "line") {
    data = [
      {
        x: xs,
        y: ys,
        type: "scatter",
        mode: "lines+markers",
        line: { color: PALETTE[0], width: 2.5, shape: "spline" },
        marker: { color: PALETTE[0], size: 6 },
        fill: "tozeroy",
        fillcolor: "rgba(0,113,227,0.08)",
      },
    ];
  } else if (spec.chart_type === "pie") {
    data = [
      {
        labels: xs,
        values: ys,
        type: "pie",
        hole: 0.62, // donut reads more modern than a full pie
        marker: { colors: PALETTE, line: { color: "#ffffff", width: 2 } },
        textposition: "outside",
        automargin: true,
        sort: false,
      },
    ];
  } else {
    // bar (default)
    data = [
      {
        x: xs,
        y: ys,
        type: "bar",
        marker: { color: PALETTE[0] },
        width: 0.62,
      },
    ];
  }

  let layout: Record<string, unknown> = BASE_LAYOUT;
  let height = 320;

  if (spec.chart_type === "pie") {
    layout = { ...BASE_LAYOUT, margin: { l: 8, r: 8, t: 8, b: 8 } };
  } else if (spec.chart_type === "hbar") {
    layout = {
      ...BASE_LAYOUT,
      margin: { l: 140, r: 16, t: 8, b: 40 },
      // Result is ordered desc; reverse so the largest sits on top.
      yaxis: { ...BASE_LAYOUT.yaxis, autorange: "reversed" },
    };
    height = Math.max(320, rows.length * 30);
  }

  return (
    <Plot
      data={data as never}
      layout={layout as never}
      config={CONFIG as never}
      style={{ width: "100%", height: `${height}px` }}
      useResizeHandler
    />
  );
}
