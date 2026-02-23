import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Hero from './sections/Hero';
import Journey from './sections/Journey';
import Specialties from './sections/Specialties';
import Contact from './sections/Contact';
import Footer from './components/Footer';
import ServiceDetail from './sections/ServiceDetail';

function HomePage() {
  return (
    <>
      <Hero />
      <Journey />
      <Specialties />
      <Contact />
    </>
  );
}

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-white">
        <Navbar />
        <main>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/services/:slug" element={<ServiceDetail />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </BrowserRouter>
  );
}

export default App;
