import Navbar from './components/Navbar';
import Hero from './sections/Hero';
import Journey from './sections/Journey';
import Specialties from './sections/Specialties';
import TopDoctors from './sections/TopDoctors';
import Features from './sections/Features';
import Contact from './sections/Contact';
import Footer from './components/Footer';

function App() {
  return (
    <div className="min-h-screen bg-white">
      <Navbar />
      <main>
        <Hero />
        <Journey />
        <Specialties />
        <TopDoctors />
        <Features />
        <Contact />
      </main>
      <Footer />
    </div>
  );
}

export default App;
