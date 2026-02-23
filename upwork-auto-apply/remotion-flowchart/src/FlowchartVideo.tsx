import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Sequence,
} from "remotion";
import React from "react";

// ─── Types ───────────────────────────────────────────────────────────────────

interface FlowchartNode {
  id: string;
  label: string;
  icon: string;
  color: string;
}

interface FlowchartEdge {
  from: string;
  to: string;
  label: string;
}

type LayoutStyle = "horizontal" | "vertical" | "zigzag";

interface FlowchartVideoProps {
  title: string;
  nodes: FlowchartNode[];
  edges: FlowchartEdge[];
  style: LayoutStyle;
  duration_seconds: number;
}

// ─── Icon Components ─────────────────────────────────────────────────────────

const IconSvg: React.FC<{ type: string; color: string; size?: number }> = ({
  type,
  color,
  size = 32,
}) => {
  const props = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: color,
    strokeWidth: 1.8,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
  };

  switch (type) {
    case "inbox":
      return (
        <svg {...props}>
          <rect x="3" y="5" width="18" height="14" rx="2" />
          <polyline points="3,7 12,13 21,7" />
        </svg>
      );
    case "brain":
      return (
        <svg {...props}>
          <circle cx="12" cy="12" r="8" />
          <path d="M12,4 C12,4 8,8 8,12 C8,16 12,20 12,20" />
          <path d="M12,4 C12,4 16,8 16,12 C16,16 12,20 12,20" />
          <line x1="4" y1="12" x2="20" y2="12" />
        </svg>
      );
    case "email":
      return (
        <svg {...props}>
          <rect x="2" y="5" width="16" height="12" rx="2" />
          <polyline points="2,7 10,13 18,7" />
          <line x1="18" y1="11" x2="22" y2="7" />
          <line x1="18" y1="11" x2="22" y2="15" />
        </svg>
      );
    case "database":
      return (
        <svg {...props}>
          <ellipse cx="12" cy="6" rx="8" ry="3" />
          <path d="M4,6 L4,18 C4,19.7 7.6,21 12,21 C16.4,21 20,19.7 20,18 L20,6" />
          <path d="M4,12 C4,13.7 7.6,15 12,15 C16.4,15 20,13.7 20,12" />
        </svg>
      );
    case "chart":
      return (
        <svg {...props}>
          <rect x="3" y="12" width="4" height="8" rx="1" fill={color} opacity="0.3" />
          <rect x="10" y="8" width="4" height="12" rx="1" fill={color} opacity="0.3" />
          <rect x="17" y="4" width="4" height="16" rx="1" fill={color} opacity="0.3" />
        </svg>
      );
    case "gear":
      return (
        <svg {...props}>
          <circle cx="12" cy="12" r="3" />
          <path d="M12,1 L12,4 M12,20 L12,23 M4.2,4.2 L6.3,6.3 M17.7,17.7 L19.8,19.8 M1,12 L4,12 M20,12 L23,12 M4.2,19.8 L6.3,17.7 M17.7,6.3 L19.8,4.2" />
        </svg>
      );
    case "robot":
      return (
        <svg {...props}>
          <rect x="5" y="8" width="14" height="12" rx="3" />
          <circle cx="9" cy="14" r="1.5" fill={color} />
          <circle cx="15" cy="14" r="1.5" fill={color} />
          <line x1="12" y1="4" x2="12" y2="8" />
          <circle cx="12" cy="3" r="1.5" />
        </svg>
      );
    case "phone":
      return (
        <svg {...props}>
          <rect x="7" y="2" width="10" height="20" rx="2" />
          <line x1="10" y1="18" x2="14" y2="18" />
        </svg>
      );
    case "calendar":
      return (
        <svg {...props}>
          <rect x="3" y="5" width="18" height="16" rx="2" />
          <line x1="3" y1="10" x2="21" y2="10" />
          <line x1="8" y1="2" x2="8" y2="6" />
          <line x1="16" y1="2" x2="16" y2="6" />
        </svg>
      );
    case "filter":
      return (
        <svg {...props}>
          <polygon points="2,4 22,4 14,14 14,21 10,21 10,14" />
        </svg>
      );
    case "send":
      return (
        <svg {...props}>
          <path d="M22,2 L11,13" />
          <polygon points="22,2 15,22 11,13 2,9" />
        </svg>
      );
    case "check":
      return (
        <svg {...props}>
          <circle cx="12" cy="12" r="9" />
          <polyline points="8,12 11,15 16,9" />
        </svg>
      );
    case "webhook":
      return (
        <svg {...props}>
          <path d="M13,2 L6,12 L10,12 L11,22 L18,12 L14,12 Z" fill={color} opacity="0.3" />
        </svg>
      );
    case "api":
      return (
        <svg {...props}>
          <polyline points="8,4 3,12 8,20" />
          <polyline points="16,4 21,12 16,20" />
          <line x1="14" y1="6" x2="10" y2="18" />
        </svg>
      );
    case "spreadsheet":
      return (
        <svg {...props}>
          <rect x="3" y="3" width="18" height="18" rx="2" />
          <line x1="3" y1="9" x2="21" y2="9" />
          <line x1="3" y1="15" x2="21" y2="15" />
          <line x1="9" y1="3" x2="9" y2="21" />
          <line x1="15" y1="3" x2="15" y2="21" />
        </svg>
      );
    case "slack":
      return (
        <svg {...props}>
          <line x1="7" y1="4" x2="7" y2="20" strokeWidth="2.5" />
          <line x1="17" y1="4" x2="17" y2="20" strokeWidth="2.5" />
          <line x1="3" y1="9" x2="21" y2="9" strokeWidth="2.5" />
          <line x1="3" y1="16" x2="21" y2="16" strokeWidth="2.5" />
        </svg>
      );
    case "crm":
      return (
        <svg {...props}>
          <circle cx="9" cy="8" r="3" />
          <circle cx="17" cy="8" r="3" />
          <path d="M3,20 C3,16 6,14 9,14 C10.5,14 11.5,14.5 12,15" />
          <path d="M12,15 C12.5,14.5 14,14 17,14 C20,14 23,16 23,20" />
        </svg>
      );
    default:
      return (
        <svg {...props}>
          <circle cx="12" cy="12" r="8" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <circle cx="12" cy="16" r="0.5" fill={color} />
        </svg>
      );
  }
};

// ─── Layout Helpers ──────────────────────────────────────────────────────────

interface NodePosition {
  x: number;
  y: number;
}

const NODE_WIDTH = 220;
const NODE_HEIGHT = 90;

function getNodePositions(
  nodes: FlowchartNode[],
  style: LayoutStyle,
  canvasWidth: number,
  canvasHeight: number
): NodePosition[] {
  const count = nodes.length;
  const positions: NodePosition[] = [];

  // Reserve space for title at top
  const topMargin = 120;
  const usableHeight = canvasHeight - topMargin;

  if (style === "horizontal") {
    const totalWidth = count * NODE_WIDTH + (count - 1) * 80;
    const startX = (canvasWidth - totalWidth) / 2;
    const centerY = topMargin + usableHeight / 2 - NODE_HEIGHT / 2;

    for (let i = 0; i < count; i++) {
      positions.push({
        x: startX + i * (NODE_WIDTH + 80),
        y: centerY,
      });
    }
  } else if (style === "vertical") {
    const gap = 40;
    const totalHeight = count * NODE_HEIGHT + (count - 1) * gap;
    const startY = topMargin + (usableHeight - totalHeight) / 2;
    const centerX = canvasWidth / 2 - NODE_WIDTH / 2;

    for (let i = 0; i < count; i++) {
      positions.push({
        x: centerX,
        y: startY + i * (NODE_HEIGHT + gap),
      });
    }
  } else {
    // zigzag
    const gap = 30;
    const totalHeight = count * NODE_HEIGHT + (count - 1) * gap;
    const startY = topMargin + (usableHeight - totalHeight) / 2;
    const centerX = canvasWidth / 2 - NODE_WIDTH / 2;
    const offset = 180;

    for (let i = 0; i < count; i++) {
      positions.push({
        x: centerX + (i % 2 === 0 ? -offset : offset),
        y: startY + i * (NODE_HEIGHT + gap),
      });
    }
  }

  return positions;
}

// ─── Arrow Component ─────────────────────────────────────────────────────────

const AnimatedArrow: React.FC<{
  fromPos: NodePosition;
  toPos: NodePosition;
  label: string;
  progress: number;
  style: LayoutStyle;
}> = ({ fromPos, toPos, label, progress, style }) => {
  if (progress <= 0) return null;

  // Compute connection points based on layout
  let startX: number, startY: number, endX: number, endY: number;

  if (style === "horizontal") {
    startX = fromPos.x + NODE_WIDTH;
    startY = fromPos.y + NODE_HEIGHT / 2;
    endX = toPos.x;
    endY = toPos.y + NODE_HEIGHT / 2;
  } else if (style === "vertical") {
    startX = fromPos.x + NODE_WIDTH / 2;
    startY = fromPos.y + NODE_HEIGHT;
    endX = toPos.x + NODE_WIDTH / 2;
    endY = toPos.y;
  } else {
    // zigzag: connect from bottom of one to top of next
    startX = fromPos.x + NODE_WIDTH / 2;
    startY = fromPos.y + NODE_HEIGHT;
    endX = toPos.x + NODE_WIDTH / 2;
    endY = toPos.y;
  }

  const dx = endX - startX;
  const dy = endY - startY;

  // Current animated end point
  const currentEndX = startX + dx * Math.min(progress, 1);
  const currentEndY = startY + dy * Math.min(progress, 1);

  // Arrow head
  const angle = Math.atan2(dy, dx);
  const headLen = 12;
  const arrowX1 = currentEndX - headLen * Math.cos(angle - Math.PI / 6);
  const arrowY1 = currentEndY - headLen * Math.sin(angle - Math.PI / 6);
  const arrowX2 = currentEndX - headLen * Math.cos(angle + Math.PI / 6);
  const arrowY2 = currentEndY - headLen * Math.sin(angle + Math.PI / 6);

  // Label position (midpoint)
  const labelX = (startX + endX) / 2;
  const labelY = (startY + endY) / 2;
  const labelOpacity = interpolate(progress, [0.5, 1], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <svg
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        pointerEvents: "none",
      }}
    >
      {/* Line */}
      <line
        x1={startX}
        y1={startY}
        x2={currentEndX}
        y2={currentEndY}
        stroke="rgba(255,255,255,0.5)"
        strokeWidth={2.5}
        strokeDasharray="8,4"
      />
      {/* Arrow head */}
      {progress >= 0.9 && (
        <polygon
          points={`${currentEndX},${currentEndY} ${arrowX1},${arrowY1} ${arrowX2},${arrowY2}`}
          fill="rgba(255,255,255,0.7)"
        />
      )}
      {/* Edge label */}
      {label && (
        <g opacity={labelOpacity}>
          <rect
            x={labelX - 50}
            y={labelY - 14}
            width={100}
            height={24}
            rx={12}
            fill="rgba(30,30,30,0.85)"
            stroke="rgba(255,255,255,0.15)"
            strokeWidth={1}
          />
          <text
            x={labelX}
            y={labelY + 4}
            textAnchor="middle"
            fill="rgba(255,255,255,0.75)"
            fontSize={11}
            fontFamily="Inter, system-ui, sans-serif"
          >
            {label}
          </text>
        </g>
      )}
    </svg>
  );
};

// ─── Node Component ──────────────────────────────────────────────────────────

const FlowchartNodeBox: React.FC<{
  node: FlowchartNode;
  position: NodePosition;
  animProgress: number;
  isLast: boolean;
  glowPulse: number;
}> = ({ node, position, animProgress, isLast, glowPulse }) => {
  if (animProgress <= 0) return null;

  const scale = interpolate(animProgress, [0, 1], [0.3, 1], {
    extrapolateRight: "clamp",
  });
  const opacity = interpolate(animProgress, [0, 0.5], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Glow for last node
  const glowSize = isLast ? interpolate(glowPulse, [0, 1], [0, 15]) : 0;

  return (
    <div
      style={{
        position: "absolute",
        left: position.x,
        top: position.y,
        width: NODE_WIDTH,
        height: NODE_HEIGHT,
        transform: `scale(${scale})`,
        opacity,
        display: "flex",
        flexDirection: "row",
        alignItems: "center",
        gap: 14,
        padding: "0 20px",
        borderRadius: 16,
        background: `linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.03) 100%)`,
        border: `1.5px solid ${node.color}55`,
        boxShadow: `0 4px 24px rgba(0,0,0,0.4), 0 0 ${glowSize}px ${node.color}88`,
        backdropFilter: "blur(8px)",
      }}
    >
      {/* Color accent bar */}
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 12,
          bottom: 12,
          width: 4,
          borderRadius: 2,
          background: node.color,
        }}
      />

      {/* Icon */}
      <div
        style={{
          flexShrink: 0,
          width: 44,
          height: 44,
          borderRadius: 10,
          background: `${node.color}20`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <IconSvg type={node.icon} color={node.color} size={26} />
      </div>

      {/* Label */}
      <div
        style={{
          color: "#FFFFFF",
          fontSize: 16,
          fontWeight: 600,
          fontFamily: "Inter, system-ui, sans-serif",
          lineHeight: 1.3,
          letterSpacing: "-0.01em",
        }}
      >
        {node.label}
      </div>
    </div>
  );
};

// ─── Main Component ──────────────────────────────────────────────────────────

export const FlowchartVideo: React.FC<FlowchartVideoProps> = ({
  title,
  nodes,
  edges,
  style,
  duration_seconds,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height, durationInFrames } = useVideoConfig();

  // ── Title animation ──
  const titleOpacity = interpolate(frame, [0, 30], [0, 1], {
    extrapolateRight: "clamp",
  });
  const titleY = interpolate(frame, [0, 30], [-20, 0], {
    extrapolateRight: "clamp",
  });

  // ── Node positions ──
  const positions = getNodePositions(nodes, style, width, height);

  // ── Node appearance (spring animation, staggered) ──
  const NODE_STAGGER = 25; // frames between each node
  const NODE_START = 20; // first node starts at frame 20

  const nodeProgresses = nodes.map((_, i) => {
    const delay = NODE_START + i * NODE_STAGGER;
    return spring({
      frame: frame - delay,
      fps,
      config: {
        damping: 14,
        stiffness: 120,
        mass: 0.8,
      },
    });
  });

  // ── Edge animation ──
  // Each edge animates after both connected nodes are visible
  const edgeProgresses = edges.map((edge) => {
    const fromIdx = nodes.findIndex((n) => n.id === edge.from);
    const toIdx = nodes.findIndex((n) => n.id === edge.to);
    if (fromIdx === -1 || toIdx === -1) return 0;

    // Edge starts after the target node begins appearing
    const edgeStartFrame =
      NODE_START + Math.max(fromIdx, toIdx) * NODE_STAGGER + 10;
    const edgeDuration = 20;

    return interpolate(frame, [edgeStartFrame, edgeStartFrame + edgeDuration], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
  });

  // ── Final glow pulse on last node ──
  const finalGlowStart = durationInFrames - 30;
  const glowPulse =
    frame >= finalGlowStart
      ? interpolate(
          frame,
          [finalGlowStart, finalGlowStart + 15, finalGlowStart + 30],
          [0, 1, 0.6],
          { extrapolateRight: "clamp" }
        )
      : 0;

  // ── Subtle grid background ──
  const gridOpacity = interpolate(frame, [0, 40], [0, 0.06], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#000000",
        fontFamily: "Inter, system-ui, sans-serif",
      }}
    >
      {/* Background grid pattern */}
      <svg
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          opacity: gridOpacity,
        }}
      >
        <defs>
          <pattern
            id="grid"
            width="40"
            height="40"
            patternUnits="userSpaceOnUse"
          >
            <path
              d="M 40 0 L 0 0 0 40"
              fill="none"
              stroke="white"
              strokeWidth="0.5"
            />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
      </svg>

      {/* Radial gradient overlay */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background:
            "radial-gradient(ellipse at 50% 40%, rgba(79,70,229,0.08) 0%, transparent 70%)",
        }}
      />

      {/* Title */}
      <div
        style={{
          position: "absolute",
          top: 36,
          left: 0,
          right: 0,
          textAlign: "center",
          opacity: titleOpacity,
          transform: `translateY(${titleY}px)`,
        }}
      >
        <div
          style={{
            fontSize: 38,
            fontWeight: 700,
            color: "#FFFFFF",
            letterSpacing: "-0.02em",
          }}
        >
          {title}
        </div>
        <div
          style={{
            marginTop: 8,
            width: 60,
            height: 3,
            borderRadius: 2,
            background: "linear-gradient(90deg, #4F46E5, #7C3AED)",
            margin: "8px auto 0",
            opacity: titleOpacity,
          }}
        />
      </div>

      {/* Edges (rendered behind nodes) */}
      {edges.map((edge, i) => {
        const fromIdx = nodes.findIndex((n) => n.id === edge.from);
        const toIdx = nodes.findIndex((n) => n.id === edge.to);
        if (fromIdx === -1 || toIdx === -1) return null;

        return (
          <AnimatedArrow
            key={`edge-${i}`}
            fromPos={positions[fromIdx]}
            toPos={positions[toIdx]}
            label={edge.label}
            progress={edgeProgresses[i]}
            style={style}
          />
        );
      })}

      {/* Nodes */}
      {nodes.map((node, i) => (
        <FlowchartNodeBox
          key={node.id}
          node={node}
          position={positions[i]}
          animProgress={nodeProgresses[i]}
          isLast={i === nodes.length - 1}
          glowPulse={i === nodes.length - 1 ? glowPulse : 0}
        />
      ))}
    </AbsoluteFill>
  );
};
