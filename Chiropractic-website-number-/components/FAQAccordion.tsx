import { useState } from 'react';
import { ChevronDown } from 'lucide-react';

interface FAQItem {
  question: string;
  answer: string;
}

interface FAQAccordionProps {
  items: FAQItem[];
}

export default function FAQAccordion({ items }: FAQAccordionProps) {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  const toggle = (index: number) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <div className="space-y-3">
      {items.map((item, index) => (
        <div
          key={index}
          className="rounded-2xl border border-gray-100 bg-white overflow-hidden transition-all duration-200"
        >
          <button
            onClick={() => toggle(index)}
            className="w-full flex items-center justify-between gap-4 p-4 sm:p-6 text-left hover:bg-gray-50/50 transition-colors"
          >
            <span className="font-semibold text-gray-900 text-sm sm:text-base">
              {item.question}
            </span>
            <ChevronDown
              className={`text-[#22C55E] shrink-0 transition-transform duration-200 ${
                openIndex === index ? 'rotate-180' : ''
              }`}
              size={20}
            />
          </button>
          <div
            className={`grid transition-all duration-200 ${
              openIndex === index ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'
            }`}
          >
            <div className="overflow-hidden">
              <p className="px-4 pb-4 sm:px-6 sm:pb-6 text-gray-600 text-sm leading-relaxed">
                {item.answer}
              </p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
