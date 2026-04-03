"use client"
import { useEffect, useRef, useState } from "react"
import * as d3 from "d3"
import { AttackGraph as AttackGraphType, GraphNode } from "@/types"

const SEV_COLORS: Record<string, string> = {
  critical: "#E24B4A",
  high: "#EF9F27",
  medium: "#BA7517",
  low: "#378ADD",
}

interface Props {
  data: AttackGraphType
}

export default function AttackGraph({ data }: Props) {
  const svgRef = useRef<SVGSVGElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [size, setSize] = useState<{ width: number; height: number }>({
    width: 0,
    height: 0,
  })

  useEffect(() => {
    if (!containerRef.current) return
    const el = containerRef.current

    const update = () => {
      const rect = el.getBoundingClientRect()
      const width = Math.max(0, Math.floor(rect.width))
      // Keep height fixed to avoid unexpected layout changes.
      const height = 500
      setSize((prev) => (prev.width === width && prev.height === height ? prev : { width, height }))
    }

    update()
    const ro = new ResizeObserver(() => update())
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  useEffect(() => {
    if (!svgRef.current || !data.nodes.length) return

    const width = size.width || svgRef.current.clientWidth || 800
    const height = size.height || 500

    d3.select(svgRef.current).selectAll("*").remove()

    const svg = d3
      .select(svgRef.current)
      .attr("viewBox", `0 0 ${width} ${height}`)
      .attr("preserveAspectRatio", "xMidYMid meet")

    const gRoot = svg.append("g").attr("class", "graph-root")

    // Arrow marker
    svg.append("defs").append("marker")
      .attr("id", "arrowhead")
      .attr("viewBox", "0 0 10 10")
      .attr("refX", 18)
      .attr("refY", 5)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M2,1 L8,5 L2,9")
      .attr("fill", "none")
      .attr("stroke", "#555")
      .attr("stroke-width", 1.5)

    const simulation = d3
      .forceSimulation(data.nodes as d3.SimulationNodeDatum[])
      .force(
        "link",
        d3
          .forceLink(data.edges)
          .id((d: d3.SimulationNodeDatum) => (d as GraphNode).id)
          .distance(45)
      )
      .force("charge", d3.forceManyBody().strength(-120).distanceMax(250))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide(18))
      .alphaDecay(0.06)

    const render = () => {
      link
        .attr(
          "x1",
          (d: d3.SimulationLinkDatum<d3.SimulationNodeDatum>) =>
            (d.source as d3.SimulationNodeDatum).x || 0
        )
        .attr(
          "y1",
          (d: d3.SimulationLinkDatum<d3.SimulationNodeDatum>) =>
            (d.source as d3.SimulationNodeDatum).y || 0
        )
        .attr(
          "x2",
          (d: d3.SimulationLinkDatum<d3.SimulationNodeDatum>) =>
            (d.target as d3.SimulationNodeDatum).x || 0
        )
        .attr(
          "y2",
          (d: d3.SimulationLinkDatum<d3.SimulationNodeDatum>) =>
            (d.target as d3.SimulationNodeDatum).y || 0
        )

      node.attr("transform", (d: any) => `translate(${d.x || 0},${d.y || 0})`)
    }

    const link = gRoot
      .append("g")
      .selectAll("line")
      .data(data.edges)
      .join("line")
      .attr("stroke", "#4B5563")
      .attr("stroke-width", 1)
      .attr("marker-end", "url(#arrowhead)")

    const node = gRoot
      .append("g")
      .selectAll("g")
      .data(data.nodes)
      .join("g")
      .attr("cursor", "pointer")
      .call(
        d3.drag<any, GraphNode>()
          .on("start", (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart()
            ;(d as d3.SimulationNodeDatum).fx = event.x
            ;(d as d3.SimulationNodeDatum).fy = event.y
          })
          .on("drag", (event, d) => {
            ;(d as d3.SimulationNodeDatum).fx = event.x
            ;(d as d3.SimulationNodeDatum).fy = event.y
          })
          .on("end", (event, d) => {
            if (!event.active) simulation.alphaTarget(0)
            ;(d as d3.SimulationNodeDatum).fx = null
            ;(d as d3.SimulationNodeDatum).fy = null

            // After user interaction, let it settle briefly, then stop again so
            // the graph doesn't keep drifting.
            window.setTimeout(() => simulation.stop(), 700)
          })
      )

    // Circle
    node.append("circle")
      .attr("r", (d: GraphNode) => d.inChain ? 16 : 10)
      .attr("fill", (d: GraphNode) => {
        if (d.inChain) return SEV_COLORS[d.severity || "low"]
        if (d.hasVuln) return SEV_COLORS[d.severity || "low"] + "88"
        return "#374151"
      })
      .attr("stroke", (d: GraphNode) => d.inChain ? SEV_COLORS[d.severity || "low"] : "#4B5563")
      .attr("stroke-width", (d: GraphNode) => d.inChain ? 2 : 1)

    // Pulse animation for chain nodes
    node.filter((d: GraphNode) => d.inChain)
      .append("circle")
      .attr("r", 18)
      .attr("fill", "none")
      .attr("stroke", (d: GraphNode) => SEV_COLORS[d.severity || "low"])
      .attr("stroke-width", 1)
      .attr("opacity", 0.5)
      .append("animate")
      .attr("attributeName", "r")
      .attr("values", "16;22;16")
      .attr("dur", "2s")
      .attr("repeatCount", "indefinite")

    // Label
    node.append("text")
      .attr("dy", 26)
      .attr("text-anchor", "middle")
      .attr("fill", "#D1D5DB")
      .attr("font-size", "10")
      .attr("font-family", "monospace")
      .text((d: GraphNode) => d.label.slice(0, 14))

    // Enable pan/zoom so large graphs don't look like they're "floating" off-screen.
    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.25, 3])
      .on("zoom", (event) => {
        gRoot.attr("transform", event.transform)
      })

    svg.call(zoom as any)

    // Pre-tick the simulation to settle positions, then fit-to-view once.
    simulation.stop()
    for (let i = 0; i < 140; i++) simulation.tick()

    // Draw once with the settled positions.
    render()

    const xs = (data.nodes as any[]).map((n) => n.x ?? 0)
    const ys = (data.nodes as any[]).map((n) => n.y ?? 0)
    const minX = Math.min(...xs)
    const maxX = Math.max(...xs)
    const minY = Math.min(...ys)
    const maxY = Math.max(...ys)

    const graphW = Math.max(1, maxX - minX)
    const graphH = Math.max(1, maxY - minY)
    const pad = 60
    const scale = Math.max(
      0.25,
      Math.min((width - pad) / graphW, (height - pad) / graphH)
    )

    const cx = (minX + maxX) / 2
    const cy = (minY + maxY) / 2
    const initial = d3.zoomIdentity
      .translate(width / 2 - scale * cx, height / 2 - scale * cy)
      .scale(scale)

    svg.call(zoom.transform as any, initial)

    // Only animate during interactions (drag restarts the simulation).
    simulation.on("tick", render)

    return () => { simulation.stop() }
  }, [data, size.width])

  return (
    <div ref={containerRef} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <div className="flex items-center gap-4 mb-4 text-xs text-gray-500">
        <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-red-500 inline-block"/>Critical chain node</span>
        <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-yellow-500 inline-block"/>High severity</span>
        <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-gray-600 inline-block"/>Clean</span>
      </div>
      <svg ref={svgRef} className="w-full" style={{ height: 500 }} />
    </div>
  )
}
