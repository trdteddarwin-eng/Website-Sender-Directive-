import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { CheckCircle, ChevronRight, ArrowRight, ArrowLeft, Phone } from 'lucide-react';
import { services } from '../data/services';
import FAQAccordion from '../components/FAQAccordion';
import { useEffect } from 'react';

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.4, 0, 0.2, 1] } },
};

export default function ServiceDetail() {
  const { slug } = useParams<{ slug: string }>();
  const service = services.find((s) => s.slug === slug);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [slug]);

  if (!service) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-white px-4">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Service Not Found</h1>
        <p className="text-gray-600 mb-8">The service you're looking for doesn't exist.</p>
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-[#22C55E] font-medium hover:underline"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Home
        </Link>
      </div>
    );
  }

  const Icon = service.icon;
  const otherServices = services.filter((s) => s.slug !== slug).slice(0, 3);

  return (
    <>
      {/* Hero */}
      <section className="relative pt-28 pb-20 sm:pt-36 sm:pb-28 bg-gradient-to-br from-[#052e16] via-[#14532d] to-[#22C55E] overflow-hidden">
        {/* Decorative blurs */}
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-[#16A34A]/20 rounded-full blur-[120px]" />
        <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-[#22C55E]/30 rounded-full blur-[100px]" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-white/[0.02] rounded-full" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          {/* Breadcrumb */}
          <nav className="flex flex-wrap items-center gap-2 text-xs sm:text-sm text-white/50 mb-8">
            <Link to="/" className="hover:text-white transition-colors">
              Home
            </Link>
            <ChevronRight size={14} />
            <Link to="/#services" className="hover:text-white transition-colors">
              Services
            </Link>
            <ChevronRight size={14} />
            <span className="text-white font-medium">{service.title}</span>
          </nav>

          <div className="grid lg:grid-cols-2 gap-10 lg:gap-16 items-center">
            <motion.div initial="hidden" animate="visible" variants={fadeUp}>
              <div className="flex flex-wrap items-center gap-3 mb-6">
                <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm text-white text-sm font-medium px-4 py-2 rounded-full border border-white/10">
                  <Icon size={16} />
                  {service.title}
                </div>
                <div className="inline-flex items-center gap-2 bg-green-500/20 backdrop-blur-sm text-green-300 text-sm font-medium px-4 py-2 rounded-full border border-green-500/20">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-green-400" />
                  </span>
                  Same-Day Appointments
                </div>
              </div>
              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-6 leading-tight">
                {service.title}
              </h1>
              <p className="text-lg text-white/70 max-w-lg leading-relaxed mb-8">
                {service.heroSubtitle}
              </p>
              <a
                href="tel:+15162218515"
                className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm text-white font-semibold px-7 py-3.5 rounded-full hover:bg-white/20 transition-colors text-sm border border-white/20"
              >
                <Phone size={16} />
                Call (516) 221-8515
              </a>
            </motion.div>

            {/* Hero image */}
            <div className="relative hidden lg:block">
              <div className="w-full aspect-[4/3] rounded-3xl overflow-hidden ring-1 ring-white/10 shadow-2xl">
                <img
                  src={service.imagePath}
                  alt={service.title}
                  className="w-full h-full object-cover"
                />
              </div>
              <div className="absolute -bottom-4 -left-4 w-32 h-32 bg-[#16A34A]/30 rounded-full blur-2xl" />
            </div>
          </div>
        </div>
      </section>

      {/* About + Benefits */}
      <section className="py-16 sm:py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-5 gap-10 lg:gap-16">
            {/* Description */}
            <motion.div
              className="lg:col-span-3"
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: '-80px' }}
              variants={fadeUp}
            >
              {/* Mobile image */}
              <div className="lg:hidden w-full aspect-[16/9] rounded-2xl overflow-hidden mb-8 bg-gradient-to-br from-[#22C55E]/10 to-[#16A34A]/10">
                <img
                  src={service.imagePath}
                  alt={service.title}
                  className="w-full h-full object-cover"
                />
              </div>

              <p className="text-[#22C55E] font-semibold text-sm mb-3 uppercase tracking-wider">
                About This Service
              </p>
              <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-900 mb-8">
                What Is{' '}
                <span className="bg-gradient-to-r from-[#22C55E] to-[#16A34A] bg-clip-text text-transparent">
                  {service.title}
                </span>
                ?
              </h2>
              <div className="space-y-5 text-gray-600 leading-relaxed text-[15px]">
                {service.detailedDescription.map((paragraph, i) => (
                  <p key={i}>{paragraph}</p>
                ))}
              </div>
            </motion.div>

            {/* Benefits sidebar */}
            <motion.div
              className="lg:col-span-2"
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: '-80px' }}
              variants={fadeUp}
            >
              <div className="bg-gradient-to-br from-[#f0fdf4] to-white rounded-2xl p-6 sm:p-8 border border-gray-100 sticky top-28">
                <h3 className="text-lg font-bold text-gray-900 mb-5">Key Benefits</h3>
                <div className="space-y-4">
                  {service.benefits.map((benefit, i) => (
                    <div key={i} className="flex items-start gap-3">
                      <div className="w-6 h-6 rounded-full bg-gradient-to-br from-[#22C55E] to-[#16A34A] flex items-center justify-center shrink-0 mt-0.5">
                        <CheckCircle className="text-white" size={14} />
                      </div>
                      <p className="text-gray-700 text-sm leading-relaxed">{benefit}</p>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* What to Expect */}
      <section className="py-16 sm:py-20 bg-[#F9FAFB]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            className="text-center mb-14"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-80px' }}
            variants={fadeUp}
          >
            <p className="text-[#22C55E] font-semibold text-sm mb-3 uppercase tracking-wider">
              Your Visit
            </p>
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-900 mb-4">
              What to{' '}
              <span className="bg-gradient-to-r from-[#22C55E] to-[#16A34A] bg-clip-text text-transparent">
                Expect
              </span>
            </h2>
            <p className="text-gray-600 max-w-xl mx-auto">
              Here's a step-by-step look at your {service.title.toLowerCase()} journey with us.
            </p>
          </motion.div>

          <div className="max-w-4xl mx-auto">
            <motion.div
              className="space-y-4"
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: '-50px' }}
              variants={{
                hidden: { opacity: 0 },
                visible: { opacity: 1, transition: { staggerChildren: 0.1 } },
              }}
            >
              {service.whatToExpect.map((step, i) => (
                <motion.div
                  key={i}
                  variants={{
                    hidden: { opacity: 0, y: 20 },
                    visible: { opacity: 1, y: 0, transition: { duration: 0.4 } },
                  }}
                  className="group flex items-start gap-5 bg-white rounded-2xl p-5 sm:p-6 border border-gray-100 hover:border-[#22C55E]/20 hover:shadow-lg hover:shadow-[#22C55E]/5 transition-all duration-300"
                >
                  <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl bg-gradient-to-br from-[#22C55E] to-[#16A34A] text-white text-sm sm:text-base font-bold flex items-center justify-center shrink-0 shadow-md shadow-[#22C55E]/25">
                    {String(i + 1).padStart(2, '0')}
                  </div>
                  <p className="text-gray-700 leading-relaxed pt-2 sm:pt-2.5 text-sm sm:text-base">
                    {step}
                  </p>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 sm:py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-80px' }}
            variants={fadeUp}
            className="rounded-2xl bg-gradient-to-r from-[#22C55E] to-[#16A34A] px-6 py-12 sm:px-12 text-center"
          >
            <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3">
              Ready to Start Your {service.title} Treatment?
            </h2>
            <p className="text-white/80 max-w-xl mx-auto mb-8">
              Schedule your visit with Dr. Bromberg at Action Chiropractic. New patients are always
              welcome — call us or visit our Westbury office today.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <a
                href="tel:+15162218515"
                className="inline-flex items-center gap-2 bg-white text-[#22C55E] font-semibold px-8 py-3.5 rounded-xl hover:bg-gray-50 transition-colors duration-300"
              >
                <Phone size={18} />
                Call (516) 221-8515
              </a>
              <Link
                to="/#contact"
                className="inline-flex items-center gap-2 bg-white/10 border border-white/20 text-white font-semibold px-8 py-3.5 rounded-xl hover:bg-white/20 transition-colors duration-300"
              >
                Contact Us
                <ArrowRight size={18} />
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-16 sm:py-20 bg-[#F9FAFB]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mx-auto">
            <motion.div
              className="text-center mb-14"
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: '-80px' }}
              variants={fadeUp}
            >
              <p className="text-[#22C55E] font-semibold text-sm mb-3 uppercase tracking-wider">
                FAQ
              </p>
              <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-900 mb-4">
                Common{' '}
                <span className="bg-gradient-to-r from-[#22C55E] to-[#16A34A] bg-clip-text text-transparent">
                  Questions
                </span>
              </h2>
              <p className="text-gray-600">
                Have questions about {service.title.toLowerCase()}? Here are answers to the most
                common ones we hear from patients.
              </p>
            </motion.div>

            <FAQAccordion items={service.faqs} />
          </div>
        </div>
      </section>

      {/* Related Services */}
      <section className="py-16 sm:py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            className="text-center mb-12"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-80px' }}
            variants={fadeUp}
          >
            <p className="text-[#22C55E] font-semibold text-sm mb-3 uppercase tracking-wider">
              Explore More
            </p>
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900">
              Other Services You May{' '}
              <span className="bg-gradient-to-r from-[#22C55E] to-[#16A34A] bg-clip-text text-transparent">
                Need
              </span>
            </h2>
          </motion.div>

          <div className="grid sm:grid-cols-3 gap-6">
            {otherServices.map((s) => {
              const OtherIcon = s.icon;
              return (
                <Link
                  key={s.slug}
                  to={`/services/${s.slug}`}
                  className="group relative bg-gradient-to-br from-[#f0fdf4] to-white rounded-2xl p-6 sm:p-8 border border-gray-100 hover:border-[#22C55E]/30 hover:shadow-xl hover:shadow-[#22C55E]/5 transition-all duration-300"
                >
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#22C55E] to-[#16A34A] flex items-center justify-center mb-5 shadow-md shadow-[#22C55E]/25">
                    <OtherIcon className="text-white" size={22} />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{s.title}</h3>
                  <p className="text-gray-600 text-sm leading-relaxed mb-4">
                    {s.shortDescription.slice(0, 100)}...
                  </p>
                  <div className="flex items-center gap-1 text-[#22C55E] text-sm font-medium group-hover:gap-2 transition-all">
                    Learn More <ArrowRight size={14} />
                  </div>
                </Link>
              );
            })}
          </div>
        </div>
      </section>
    </>
  );
}
