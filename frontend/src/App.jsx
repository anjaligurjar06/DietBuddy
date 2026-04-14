import './App.css';
import { BrowserRouter, Routes, Route } from "react-router-dom";

import LoginForm from './LoginForm';
import Preferences from './Preferences'; 

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginForm />} />
        <Route path="/preferences" element={<Preferences />} />
      </Routes>
    </BrowserRouter>
  
  );
}

export default App;
