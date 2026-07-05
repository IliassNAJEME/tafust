import { useEffect, useRef } from "react";
import * as d3 from "d3";

interface NetworkTopologyProps {
  rawResults: any[];
}

export default function NetworkTopology({ rawResults }: NetworkTopologyProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!svgRef.current || !containerRef.current || !rawResults || rawResults.length === 0) return;

    const width = containerRef.current.clientWidth;
    const height = 400;

    // Clear previous drawing
    d3.select(svgRef.current).selectAll("*").remove();

    // Data processing
    const nodesMap = new Map();
    const links: any[] = [];

    // Local machine node
    nodesMap.set("local", { id: "local", label: "Local Machine", group: "local", radius: 25 });

    rawResults.forEach((res) => {
      const portId = `port-${res.port}`;
      if (!nodesMap.has(portId)) {
        nodesMap.set(portId, { 
          id: portId, 
          label: `:${res.port}`, 
          group: "port", 
          radius: 15,
          risk: res.risk_level || "UNKNOWN"
        });
        links.push({ source: "local", target: portId, value: 2 });
      }

      if (res.proc && res.proc !== "Unknown") {
        const procId = `proc-${res.proc}`;
        if (!nodesMap.has(procId)) {
          nodesMap.set(procId, { 
            id: procId, 
            label: res.proc, 
            group: "process", 
            radius: 20 
          });
        }
        // Link port to process
        // Avoid duplicate links
        if (!links.some(l => l.source === portId && l.target === procId)) {
          links.push({ source: portId, target: procId, value: 1 });
        }
      }
    });

    const nodes = Array.from(nodesMap.values());

    const svg = d3.select(svgRef.current)
      .attr("width", width)
      .attr("height", height)
      .attr("viewBox", [0, 0, width, height]);

    // Graph physics
    const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id((d: any) => d.id).distance(60))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collide", d3.forceCollide().radius((d: any) => d.radius + 5));

    // Links
    const link = svg.append("g")
      .attr("stroke", "#1a2d4a")
      .attr("stroke-opacity", 0.6)
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke-width", (d: any) => d.value);

    // Nodes
    const getFillColor = (d: any) => {
      if (d.group === "local") return "#0f1d32";
      if (d.group === "process") return "#132238";
      // Port risks
      if (d.risk === "CRITIQUE") return "#ff4757";
      if (d.risk === "ÉLEVÉ") return "#ffa502";
      if (d.risk === "MODÉRÉ") return "#f59e0b";
      return "#00ffa3"; // safe/signal
    };

    const node = svg.append("g")
      .selectAll("g")
      .data(nodes)
      .join("g")
      .call(d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended) as any);

    node.append("circle")
      .attr("r", (d: any) => d.radius)
      .attr("fill", getFillColor)
      .attr("stroke", (d: any) => d.group === "local" ? "#00ffa3" : "#1a2d4a")
      .attr("stroke-width", 2);

    node.append("text")
      .text((d: any) => d.label)
      .attr("x", (d: any) => d.radius + 4)
      .attr("y", 3)
      .attr("font-size", "10px")
      .attr("fill", "#d7e3f4")
      .attr("font-family", "JetBrains Mono");

    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      node
        .attr("transform", (d: any) => `translate(${d.x},${d.y})`);
    });

    function dragstarted(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }
    
    function dragged(event: any, d: any) {
      d.fx = event.x;
      d.fy = event.y;
    }
    
    function dragended(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    return () => {
      simulation.stop();
    };
  }, [rawResults]);

  return (
    <div ref={containerRef} className="w-full h-[400px] overflow-hidden bg-ink/50 rounded-lg border border-border">
      {(!rawResults || rawResults.length === 0) ? (
        <div className="flex h-full items-center justify-center text-sm text-subtle">
          Aucune donnée réseau à visualiser
        </div>
      ) : (
        <svg ref={svgRef} className="w-full h-full" />
      )}
    </div>
  );
}
