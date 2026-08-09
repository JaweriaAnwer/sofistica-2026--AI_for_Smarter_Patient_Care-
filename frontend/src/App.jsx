import { Routes, Route, Navigate } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { useLocation } from 'react-router-dom';
import SafetyBanner from './components/SafetyBanner';
import Sidebar from './components/Sidebar';
import Home from './pages/Home';
import CohortBuilder from './pages/CohortBuilder';
import DataQuality from './pages/DataQuality';
import CoverageExplorer from './pages/CoverageExplorer';
import useButtonRipple from './lib/useButtonRipple';

function AnimatedRoutes() {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location.pathname}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8 }}
        transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
      >
        <Routes location={location}>
          <Route path="/" element={<Home />} />
          <Route path="/cohort" element={<CohortBuilder />} />
          <Route path="/quality" element={<DataQuality />} />
          <Route path="/coverage" element={<CoverageExplorer />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </motion.div>
    </AnimatePresence>
  );
}

export default function App() {
  useButtonRipple();
  return (
    <>
      <SafetyBanner />
      <div className="app-shell">
        <Sidebar />
        <main className="main-content" style={{ marginLeft: 'var(--sidebar-w)' }}>
          <AnimatedRoutes />
        </main>
      </div>
    </>
  );
}
