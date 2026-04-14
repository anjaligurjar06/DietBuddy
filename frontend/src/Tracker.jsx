import { useState } from "react";
import MacroPieChart from "./MacroPieChart";

function Tracker() {
  const [macros, setMacros] = useState({
    protein: 0,
    carbs: 0,
    fats: 0,
  });

  const [total, setTotal] = useState(0);
  const maxLimit = 100;

  const foodList = [
    { name: "egg", protein: 6, carbs: 1, fats: 5 },
    { name: "rice", protein: 3, carbs: 20, fats: 1 },
    { name: "dal", protein: 8, carbs: 18, fats: 2 },
    { name: "roti", protein: 4, carbs: 15, fats: 1 },
  ];

  const handleAdd = (food) => {
    setMacros((prev) => ({
      protein: prev.protein + food.protein,
      carbs: prev.carbs + food.carbs,
      fats: prev.fats + food.fats,
    }));

    setTotal((prev) => Math.min(prev + 10, maxLimit));
  };

  const chartData = [
    { name: "Protein", value: macros.protein },
    { name: "Carbs", value: macros.carbs },
    { name: "Fats", value: macros.fats },
  ];

  return (
    <div style={{ padding: "20px" }}>
      <h3>Food Tracker</h3>

      {foodList.map((food, index) => (
        <button key={index} onClick={() => handleAdd(food)}>
          Add {food.name}
        </button>
      ))}

      {/* ✅ Progress Bar */}
      <div style={{ marginTop: "20px" }}>
        <div
          style={{
            height: "20px",
            width: "100%",
            background: "#ddd",
            borderRadius: "10px",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              height: "100%",
              width: `${(total / maxLimit) * 100}%`,
              background: "green",
              transition: "0.3s",
            }}
          />
        </div>

        <p>{total} / {maxLimit}</p>
      </div>

      {/* ✅ Pie Chart */}
      <MacroPieChart data={chartData} />
    </div>
  );
}

export default Tracker;