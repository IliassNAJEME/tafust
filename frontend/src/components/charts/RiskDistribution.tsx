import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";

interface RiskDistributionProps {
  summary: {
    nb_alertes?: number;
    nb_surveiller?: number;
    nb_legitimes?: number;
  };
}

const COLORS = {
  Alertes: "#ff4757", // danger
  Surveillance: "#ffa502", // warning
  Legitimes: "#00ffa3", // signal
};

export default function RiskDistribution({ summary }: RiskDistributionProps) {
  const data = [
    { name: "Alertes", value: summary.nb_alertes || 0 },
    { name: "Surveillance", value: summary.nb_surveiller || 0 },
    { name: "Légitimes", value: summary.nb_legitimes || 0 },
  ].filter((d) => d.value > 0);

  if (data.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-subtle">
        Pas de données pour le graphique
      </div>
    );
  }

  return (
    <div className="h-[250px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={80}
            paddingAngle={5}
            dataKey="value"
            stroke="none"
          >
            {data.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={COLORS[entry.name as keyof typeof COLORS] || "#8ba4c0"} 
                className="drop-shadow-md"
              />
            ))}
          </Pie>
          <Tooltip 
            contentStyle={{ backgroundColor: "#0b1425", borderColor: "#1a2d4a", borderRadius: "8px" }}
            itemStyle={{ color: "#d7e3f4" }}
          />
          <Legend verticalAlign="bottom" height={36} iconType="circle" />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
