import { PieChart, Pie, Cell, Tooltip, Legend } from "recharts";

function MacroPieChart({ data }) {
  const COLORS = ["#0088FE", "#00C49F", "#FFBB28"];

  return (
    <div style={{ display: "flex", justifyContent: "center" }}>
      <PieChart width={400} height={400}>
        <Pie
          data={data}          
          dataKey="value"      
          nameKey="name"
          cx="50%"
          cy="50%"
          outerRadius={120}
        >
          {data.map((entry, index) => (
            <Cell key={index} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>

        <Tooltip />
        <Legend />
      </PieChart>
    </div>
  );
}

export default MacroPieChart;