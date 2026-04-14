import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Tracker from "./Tracker";
import MacroPieChart from "./MacroPieChart";

function Preferences() {
  const [input, setInput] = useState("");
  const [foods, setFoods] = useState([]);
  const [macros, setMacros] = useState({
    protein: 0,
    carbs: 0,
    fats: 0,
  });

  const navigate = useNavigate();
    
  const foodDatabase = {
    roti: { protein: 4, carbs: 15, fats: 1 },
    rice: { protein: 3, carbs: 20, fats: 1 },
    dal: { protein: 8, carbs: 18, fats: 2 },
    egg: { protein: 6, carbs: 1, fats: 5 },
  };

    const handleAdd = () => {
    if (!input) return;

    const food = input.toLowerCase();

    if (!foodDatabase[food]) {
      alert("Food not in database");
      return;
    }

    setFoods([...foods, food]);

    setMacros((prev) => ({
      protein: prev.protein + foodDatabase[food].protein,
      carbs: prev.carbs + foodDatabase[food].carbs,
      fats: prev.fats + foodDatabase[food].fats,
    }));

    setInput("");
  };
    
  const chartData = [
    { name: "Protein", value: macros.protein },
    { name: "Carbs", value: macros.carbs },
    { name: "Fats", value: macros.fats },
  ];
  const handleContinue = () => {
  navigate("/dashboard");
};

    return (
    <div style={{ display: "flex", height: "100vh" }}>

      
      <div style={{ width: "40%", padding: "20px" }}>
        <h2>What foods do you usually eat?</h2>

        <input
          type="text"
          placeholder="e.g. roti"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleAdd();
          }}
        />

        <button onClick={handleAdd}>Add</button>

        <div>
          <h3>Your Foods:</h3>
          {foods.map((food, index) => (
            <p key={index}>{food}</p>
          ))}
        </div>

        <button onClick={handleContinue}>Continue</button>
      </div>

      {/* RIGHT SIDE (PIE CHART) */}
      <div style={{ width: "60%" }}>
        <MacroPieChart data={chartData} />
        <Tracker />
      </div>

    </div>
  );
}
  export default Preferences;