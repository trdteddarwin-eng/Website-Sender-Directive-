import { Composition } from "remotion";
import { FlowchartVideo } from "./FlowchartVideo";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="FlowchartVideo"
        component={FlowchartVideo}
        durationInFrames={240}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          title: "Lead Automation Workflow",
          nodes: [
            { id: "n1", label: "Lead Comes In", icon: "inbox", color: "#4F46E5" },
            { id: "n2", label: "AI Scores Lead", icon: "brain", color: "#7C3AED" },
            { id: "n3", label: "Email Sent", icon: "email", color: "#059669" },
            { id: "n4", label: "CRM Updated", icon: "database", color: "#D97706" },
          ],
          edges: [
            { from: "n1", to: "n2", label: "webhook" },
            { from: "n2", to: "n3", label: "if score > 7" },
            { from: "n3", to: "n4", label: "on send" },
          ],
          style: "horizontal" as const,
          duration_seconds: 8,
        }}
      />
    </>
  );
};
