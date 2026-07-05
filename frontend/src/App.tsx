import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AnimatePresence } from "framer-motion";
import MainLayout from "./layouts/MainLayout";
import Dashboard from "./pages/Dashboard";
import Results from "./pages/Results";
import History from "./pages/History";
import Settings from "./pages/Settings";

export default function App() {
  return (
    <BrowserRouter>
      <MainLayout>
        <AnimatePresence mode="wait">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/results" element={<Results />} />
            <Route path="/history" element={<History />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </AnimatePresence>
      </MainLayout>
    </BrowserRouter>
  );
}
