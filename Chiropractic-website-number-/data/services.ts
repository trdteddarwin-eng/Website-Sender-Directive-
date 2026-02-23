import {
  Activity,
  Target,
  Smile,
  Hand,
  Zap,
  ScanLine,
  StretchHorizontal,
  Heart,
  type LucideIcon,
} from 'lucide-react';

export interface ServiceFAQ {
  question: string;
  answer: string;
}

export interface Service {
  slug: string;
  title: string;
  icon: LucideIcon;
  shortDescription: string;
  heroSubtitle: string;
  detailedDescription: string[];
  whatToExpect: string[];
  benefits: string[];
  imagePath: string;
  faqs: ServiceFAQ[];
}

export const services: Service[] = [
  {
    slug: 'spinal-adjustments',
    title: 'Spinal Adjustments',
    icon: Activity,
    shortDescription:
      'Precise manual adjustments to restore proper spinal alignment and relieve nerve pressure.',
    heroSubtitle:
      'Restore your body\'s natural alignment with expert chiropractic adjustments tailored to your needs by Dr. Bromberg.',
    detailedDescription: [
      'Spinal adjustments, also known as spinal manipulation, are the foundation of chiropractic care at Action Chiropractic P.C. During an adjustment, Dr. Bromberg applies a controlled, sudden force to a specific joint in the spine. This technique corrects structural alignment issues, improves your body\'s physical function, and reduces nerve irritability that can cause pain, inflammation, and muscle tension.',
      'Misalignments in the spine — called subluxations — can develop gradually from poor posture, repetitive stress, injuries, or the natural aging process. These misalignments put pressure on surrounding nerves and tissues, leading to discomfort that can radiate throughout the body. Spinal adjustments relieve this pressure, restoring proper communication between your brain and body.',
      'At Action Chiropractic, we use a combination of manual adjustment techniques including Diversified, Thompson Drop-Table, and Activator Methods. Your treatment plan is personalized based on a thorough examination that includes posture analysis, range-of-motion testing, and when necessary, on-site digital X-rays to pinpoint the exact areas that need attention.',
    ],
    whatToExpect: [
      'A comprehensive initial consultation reviewing your health history, lifestyle, and specific concerns',
      'Physical examination including posture analysis, spinal palpation, and range-of-motion tests',
      'A clear explanation of any findings and a recommended treatment plan',
      'Gentle, precise adjustments using the technique best suited to your condition',
      'Post-adjustment guidance on stretches, exercises, or ergonomic changes to support your progress',
      'Follow-up visits to monitor improvement and adjust your plan as needed',
    ],
    benefits: [
      'Immediate relief from back pain, stiffness, and muscle tension',
      'Improved range of motion and flexibility throughout the spine',
      'Reduced nerve interference for better overall body function',
      'Enhanced posture and spinal alignment over time',
      'Drug-free approach to managing chronic and acute pain',
    ],
    imagePath: '/services/spinal-adjustments.png',
    faqs: [
      {
        question: 'Does a spinal adjustment hurt?',
        answer:
          'Most patients feel little to no pain during an adjustment. You may feel a brief sensation of pressure and sometimes hear a popping sound — this is simply gas being released from the joint. Some patients experience mild soreness for 12–24 hours after their first few sessions, similar to what you might feel after starting a new workout.',
      },
      {
        question: 'How many sessions will I need?',
        answer:
          'This depends on the nature and severity of your condition. Some patients experience significant relief after just one visit, while chronic issues may require a series of sessions over several weeks. After your initial evaluation, Dr. Bromberg will provide a personalized treatment plan with a clear timeline.',
      },
      {
        question: 'Is chiropractic adjustment safe?',
        answer:
          'Yes. Spinal adjustments performed by a licensed chiropractor are widely recognized as one of the safest, drug-free, non-invasive treatments available for musculoskeletal complaints. Serious complications are extremely rare. We conduct a thorough evaluation before any adjustment to ensure it is appropriate for you.',
      },
      {
        question: 'What is the popping sound during an adjustment?',
        answer:
          'The popping or cracking sound is called cavitation. It occurs when a quick stretch of the joint capsule releases gas bubbles from the synovial fluid. It\'s completely harmless and is not an indicator of bones cracking or grinding.',
      },
      {
        question: 'Can I get adjusted if I\'ve had back surgery?',
        answer:
          'In many cases, yes. Dr. Bromberg takes a careful approach with post-surgical patients, focusing on areas above and below the surgical site. He will review your surgical history and imaging before recommending any treatment, and may use gentler techniques such as the Activator Method.',
      },
    ],
  },
  {
    slug: 'sports-rehabilitation',
    title: 'Sports Rehabilitation',
    icon: Target,
    shortDescription:
      'Specialized rehab programs for athletes to recover from injuries and improve performance.',
    heroSubtitle:
      'Get back in the game faster with targeted sports rehabilitation and performance optimization.',
    detailedDescription: [
      'Sports injuries — whether from a weekend game or competitive athletics — require specialized care that addresses both the injury itself and the movement patterns that caused it. At Action Chiropractic, our sports rehabilitation program combines chiropractic adjustments with evidence-based rehab protocols to accelerate healing, restore function, and reduce the risk of re-injury.',
      'Common sports injuries we treat include sprains, strains, tendinitis, rotator cuff injuries, runner\'s knee, shin splints, and sports-related back pain. We go beyond symptom relief by analyzing your biomechanics to identify muscle imbalances, joint restrictions, and movement dysfunctions that may have contributed to your injury.',
      'Our approach integrates spinal and extremity adjustments, soft tissue therapies such as myofascial release, targeted exercise rehabilitation, and sport-specific functional training. Whether you\'re recovering from an acute injury or dealing with a chronic overuse condition, Dr. Bromberg designs a program to get you back to full activity safely.',
    ],
    whatToExpect: [
      'Detailed evaluation of your injury including mechanism, severity, and impact on your sport',
      'Biomechanical assessment to identify contributing factors like muscle imbalances or restricted joints',
      'A phased recovery plan: pain reduction, mobility restoration, strength rebuilding, return-to-sport',
      'Hands-on treatment including adjustments, soft tissue work, and therapeutic exercises',
      'Sport-specific drills and functional training as you near full recovery',
      'Injury prevention strategies and maintenance recommendations for long-term performance',
    ],
    benefits: [
      'Faster recovery times compared to rest-only approaches',
      'Reduced risk of re-injury through biomechanical correction',
      'Improved athletic performance and range of motion',
      'Drug-free pain management throughout the recovery process',
      'Return-to-sport guidance backed by functional testing',
    ],
    imagePath: '/services/sports-injury-rehab.png',
    faqs: [
      {
        question: 'How soon after an injury should I see a chiropractor?',
        answer:
          'The sooner the better. Early intervention can reduce inflammation, prevent compensatory movement patterns, and speed recovery. For acute injuries, we recommend scheduling within the first 48–72 hours. If your injury involves fractures, dislocations, or severe swelling, seek emergency care first.',
      },
      {
        question: 'Can chiropractic care help prevent sports injuries?',
        answer:
          'Absolutely. Regular chiropractic care keeps your joints mobile, your muscles balanced, and your nervous system functioning optimally — all of which reduce injury risk. Many athletes use chiropractic care as part of their ongoing training and prevention programs.',
      },
      {
        question: 'What sports injuries do you treat most often?',
        answer:
          'We commonly treat lower back strains, shoulder impingement, rotator cuff issues, IT band syndrome, runner\'s knee, ankle sprains, tennis/golfer\'s elbow, and neck injuries. However, we treat the full range of musculoskeletal sports injuries.',
      },
      {
        question: 'How long until I can return to my sport?',
        answer:
          'Return timelines vary based on injury type and severity. We use functional testing benchmarks — not just pain levels — to determine when you\'re truly ready. Mild injuries may resolve in 2–4 weeks, while more significant injuries can take 6–12 weeks.',
      },
    ],
  },
  {
    slug: 'posture-correction',
    title: 'Posture Correction',
    icon: Smile,
    shortDescription:
      'Comprehensive posture analysis and corrective care for desk workers and chronic pain sufferers.',
    heroSubtitle:
      'Stand taller and feel better with a personalized posture correction program built for lasting results.',
    detailedDescription: [
      'Poor posture is one of the most common yet overlooked causes of chronic pain, fatigue, and reduced quality of life. Whether it\'s from hours spent at a desk, prolonged phone use, or habitual slouching, postural imbalances place uneven stress on your spine, muscles, and joints — leading to pain that often worsens over time if left unaddressed.',
      'Our posture correction program begins with a thorough digital posture analysis that identifies deviations such as forward head posture, rounded shoulders, pelvic tilt, and spinal curvatures. We measure the degree of misalignment and create a visual baseline so you can track your improvement over the course of treatment.',
      'Treatment combines chiropractic adjustments to realign the spine with targeted strengthening and stretching exercises designed to retrain your postural muscles. We also provide ergonomic recommendations for your workspace, sleeping position, and daily habits. The result is not just better posture, but reduced pain, improved breathing, and increased energy throughout your day.',
    ],
    whatToExpect: [
      'Digital posture analysis with baseline measurements and photos for progress tracking',
      'Spinal examination to identify specific vertebral misalignments contributing to poor posture',
      'Chiropractic adjustments focused on restoring proper spinal curvature',
      'A personalized exercise program targeting weak postural muscles and tight compensating muscles',
      'Ergonomic assessment and recommendations for your work and home environment',
      'Regular progress evaluations with updated posture measurements',
    ],
    benefits: [
      'Reduced neck, shoulder, and back pain caused by postural strain',
      'Improved breathing capacity and oxygen flow from proper spinal alignment',
      'Increased energy and reduced fatigue throughout the day',
      'Better appearance and confidence from standing and sitting taller',
      'Prevention of long-term degenerative changes associated with poor posture',
    ],
    imagePath: '/services/posture-correction.png',
    faqs: [
      {
        question: 'Can posture really be corrected in adults?',
        answer:
          'Yes. While it\'s easier to address postural issues in younger patients, adults of all ages can see significant improvement. The key is consistency — combining in-office adjustments with daily exercises and ergonomic changes. Most patients notice visible improvement within 4–8 weeks.',
      },
      {
        question: 'How does poor posture cause pain?',
        answer:
          'Poor posture shifts your center of gravity, forcing certain muscles to overwork while others weaken. This imbalance puts extra stress on spinal joints, discs, and nerves. Over time, this leads to chronic pain in the neck, shoulders, upper back, and lower back, and can even contribute to headaches.',
      },
      {
        question: 'Will I need to do exercises at home?',
        answer:
          'Yes, home exercises are a critical part of posture correction. In-office adjustments realign your spine, but strengthening exercises are what teach your body to maintain that alignment. We\'ll give you a simple, manageable routine that typically takes 10–15 minutes per day.',
      },
      {
        question: 'Is tech neck a real condition?',
        answer:
          '"Tech neck" or "text neck" refers to the forward head posture that develops from looking down at phones, tablets, and laptops for extended periods. For every inch your head moves forward from its neutral position, the effective weight on your cervical spine increases by approximately 10 pounds. We see this frequently and treat it very effectively.',
      },
    ],
  },
  {
    slug: 'massage-therapy',
    title: 'Massage Therapy',
    icon: Hand,
    shortDescription:
      'Therapeutic deep tissue and soft tissue massage to complement your chiropractic treatment.',
    heroSubtitle:
      'Relieve tension and accelerate healing with therapeutic massage designed to complement your chiropractic care.',
    detailedDescription: [
      'Massage therapy is a powerful complement to chiropractic adjustments. At Action Chiropractic, our therapeutic massage services target deep muscle tension, trigger points, and fascial restrictions that contribute to pain and limited mobility. Unlike spa massage, our focus is clinical — each session is designed to support your treatment goals and accelerate recovery.',
      'Chronic muscle tension can prevent chiropractic adjustments from holding properly. When muscles around misaligned joints are tight and guarded, they pull the spine back out of alignment. By releasing this tension through targeted massage, we help your adjustments last longer and your body heal more completely.',
      'We offer deep tissue massage, myofascial release, trigger point therapy, and soft tissue mobilization. Each session is tailored to your specific needs — whether you\'re dealing with a sports injury, chronic back pain, tension headaches, or simply the accumulated stress of daily life. Dr. Bromberg coordinates your massage therapy with your overall chiropractic treatment plan for optimal results.',
    ],
    whatToExpect: [
      'A brief intake to identify your primary areas of tension, pain, and treatment goals',
      'Targeted therapeutic massage focused on problem areas rather than a full-body relaxation session',
      'Deep tissue work to release chronic muscle knots and fascial adhesions',
      'Integration with your chiropractic adjustment schedule for maximum benefit',
      'Post-session stretching recommendations and hydration guidance',
      'Regular reassessment to track muscle tension improvement alongside spinal progress',
    ],
    benefits: [
      'Reduced muscle tension that helps chiropractic adjustments hold longer',
      'Relief from chronic muscle knots, trigger points, and fascial tightness',
      'Improved blood circulation and lymphatic drainage for faster healing',
      'Decreased stress hormones and increased relaxation response',
      'Enhanced range of motion and flexibility in tight muscle groups',
    ],
    imagePath: '/services/neck-pain-relief.png',
    faqs: [
      {
        question: 'How is therapeutic massage different from spa massage?',
        answer:
          'Therapeutic massage at our clinic is medically focused. While a spa massage is designed for general relaxation, our sessions target specific problem areas contributing to your pain or dysfunction. The pressure, technique, and focus areas are guided by your clinical assessment and treatment plan.',
      },
      {
        question: 'Should I get a massage before or after my adjustment?',
        answer:
          'Both approaches have benefits. Massage before an adjustment can relax tight muscles, making the adjustment easier and more effective. Massage after can help the surrounding tissues adapt to the new alignment. Dr. Bromberg will recommend the optimal sequence for your condition.',
      },
      {
        question: 'How often should I get therapeutic massage?',
        answer:
          'For acute conditions, weekly sessions are often recommended initially. For maintenance and prevention, every 2–4 weeks is typical. The frequency depends on your condition, treatment goals, and how your body responds. We\'ll build massage into your overall care plan.',
      },
      {
        question: 'Will the massage be painful?',
        answer:
          'Deep tissue massage can involve some discomfort when working on areas of chronic tension, but it should never be unbearable. We communicate throughout the session to keep the pressure at a therapeutic level that\'s effective without being overly painful. Most patients describe it as "good pain" that brings relief.',
      },
    ],
  },
  {
    slug: 'pain-management',
    title: 'Pain Management',
    icon: Zap,
    shortDescription:
      'Drug-free pain relief solutions for back pain, neck pain, headaches, and sciatica.',
    heroSubtitle:
      'Find lasting relief from chronic pain with drug-free solutions that address the root cause, not just the symptoms.',
    detailedDescription: [
      'Chronic pain affects every aspect of your life — your work, your relationships, your sleep, and your overall well-being. At Action Chiropractic, Dr. Bromberg specializes in drug-free pain management that goes beyond symptom masking to address the underlying structural and neurological causes of your pain.',
      'Whether you\'re dealing with persistent back pain, neck pain, headaches, sciatica, or radiating nerve pain, our approach starts with a comprehensive evaluation to identify exactly what\'s causing your discomfort. We use on-site digital X-rays, orthopedic testing, and neurological screening to build a complete picture of your condition.',
      'Your personalized pain management plan may include spinal adjustments, decompression therapy, soft tissue work, targeted exercises, and ergonomic modifications. We track your progress objectively through pain scales, functional assessments, and range-of-motion measurements — so you can see real improvement over time, not just feel it. Our goal is to reduce your pain, restore your function, and give you the tools to stay pain-free long-term.',
    ],
    whatToExpect: [
      'A thorough initial evaluation including health history, pain assessment, orthopedic and neurological testing',
      'On-site digital X-rays if needed to identify structural causes of pain',
      'A clear diagnosis and explanation of what\'s causing your pain',
      'A multi-modal treatment plan combining adjustments, soft tissue therapy, and rehabilitation exercises',
      'Objective progress tracking with measurable pain and function improvements',
      'Long-term strategies to maintain relief and prevent pain recurrence',
    ],
    benefits: [
      'Significant reduction in chronic pain without medications or surgery',
      'Treatment of the root cause rather than temporary symptom relief',
      'Improved daily function — better sleep, work capacity, and quality of life',
      'Objective progress tracking so you can see measurable improvement',
      'Long-term strategies to maintain relief and prevent recurrence',
    ],
    imagePath: '/services/sciatica-treatment.png',
    faqs: [
      {
        question: 'Can chiropractic care replace pain medication?',
        answer:
          'For many patients, yes. Chiropractic care addresses the structural causes of pain, which medications only mask. Many of our patients are able to significantly reduce or eliminate their reliance on pain medications over the course of treatment. However, we always coordinate with your prescribing physician if you\'re currently on medication.',
      },
      {
        question: 'What types of pain do you treat?',
        answer:
          'We treat a wide range of musculoskeletal pain including lower back pain, upper back pain, neck pain, headaches and migraines, sciatica, shoulder pain, hip pain, and pain from disc herniations. If your pain is musculoskeletal in origin, chiropractic care can likely help.',
      },
      {
        question: 'How quickly will I feel relief?',
        answer:
          'Many patients notice some improvement after their first visit. However, lasting pain relief for chronic conditions typically develops over 2–6 weeks of consistent treatment. Acute pain often responds faster. Dr. Bromberg will give you a realistic timeline based on your specific condition.',
      },
      {
        question: 'Do I need a referral from my doctor?',
        answer:
          'No referral is needed to see Dr. Bromberg. However, we\'re happy to coordinate with your primary care physician or specialist to ensure your care is well-integrated with any other treatments you may be receiving.',
      },
    ],
  },
  {
    slug: 'xray-diagnostics',
    title: 'X-Ray & Diagnostics',
    icon: ScanLine,
    shortDescription:
      'On-site digital X-rays for accurate diagnosis and personalized treatment planning.',
    heroSubtitle:
      'Get answers fast with on-site digital X-rays and comprehensive diagnostic evaluation at Action Chiropractic.',
    detailedDescription: [
      'Accurate diagnosis is the foundation of effective treatment. At Action Chiropractic, we have state-of-the-art digital X-ray equipment on-site, allowing Dr. Bromberg to capture high-resolution images of your spine and joints right here in our Westbury office — no need for a separate radiology appointment.',
      'Digital X-rays provide immediate results with significantly less radiation exposure than traditional film X-rays. They allow us to visualize spinal alignment, disc spacing, joint degeneration, fractures, and other structural abnormalities with exceptional clarity. This information is essential for developing an accurate diagnosis and a targeted treatment plan.',
      'Our diagnostic process goes beyond imaging. Dr. Bromberg conducts a thorough physical examination including orthopedic testing, neurological screening, posture analysis, and range-of-motion assessment. When all of this information is combined with your health history and imaging results, we can pinpoint the exact cause of your symptoms and design the most effective treatment approach.',
    ],
    whatToExpect: [
      'A comprehensive health history review to understand your symptoms and background',
      'Physical examination including palpation, range-of-motion, and orthopedic tests',
      'On-site digital X-rays with immediate results — no waiting for outside reports',
      'A detailed review of your images with Dr. Bromberg, who will explain what he sees in plain language',
      'A clear diagnosis and recommended treatment plan based on your complete evaluation',
      'Referral for advanced imaging (MRI, CT) if needed for complex cases',
    ],
    benefits: [
      'Same-day imaging and results — no referrals or separate appointments needed',
      'Significantly lower radiation exposure compared to traditional X-rays',
      'Accurate diagnosis that leads to more targeted and effective treatment',
      'Visual evidence of your condition that you can see and understand',
      'A complete diagnostic picture combining imaging, exam findings, and health history',
    ],
    imagePath: '/services/wellness-programs.png',
    faqs: [
      {
        question: 'Are digital X-rays safe?',
        answer:
          'Yes. Digital X-rays use significantly less radiation than traditional film X-rays — typically 50–80% less. The radiation exposure from a spinal X-ray is comparable to the natural background radiation you receive in a few days. We follow all safety protocols and only take X-rays when clinically necessary.',
      },
      {
        question: 'Does everyone need X-rays before treatment?',
        answer:
          'Not always. Dr. Bromberg determines whether X-rays are necessary based on your symptoms, health history, and physical examination findings. X-rays are typically recommended for new patients with significant symptoms, trauma history, or when the exam reveals findings that need further investigation.',
      },
      {
        question: 'How long does the diagnostic process take?',
        answer:
          'A comprehensive new patient evaluation including X-rays typically takes about 45–60 minutes. You\'ll receive a full explanation of your findings and treatment recommendations during the same visit — no need to schedule a separate appointment for results.',
      },
      {
        question: 'Will my insurance cover diagnostic X-rays?',
        answer:
          'Most insurance plans cover diagnostic X-rays when they are medically necessary. Our office staff will verify your insurance coverage and benefits before your visit so there are no surprises. We also offer affordable self-pay rates for patients without insurance coverage.',
      },
    ],
  },
  {
    slug: 'flexibility-mobility',
    title: 'Flexibility & Mobility',
    icon: StretchHorizontal,
    shortDescription:
      'Targeted stretching and mobility exercises to restore range of motion and prevent injuries.',
    heroSubtitle:
      'Move freely and without pain through targeted mobility programs designed to restore your full range of motion.',
    detailedDescription: [
      'Restricted flexibility and limited mobility are among the most common issues that bring patients to Action Chiropractic. Whether it\'s difficulty bending down, stiffness when turning your head, or tight hips that affect your walking, these limitations often signal underlying joint restrictions, muscle imbalances, or spinal misalignments that benefit from professional care.',
      'Our flexibility and mobility program combines chiropractic adjustments to restore proper joint mechanics with targeted stretching protocols and corrective exercises. Dr. Bromberg assesses not just where you feel tight, but why — identifying the specific joints that are restricted and the muscles that have adapted to compensate for those restrictions.',
      'Unlike generic stretching routines, our program is tailored to your body\'s specific needs. We use functional movement screening to identify areas of restriction, then build a progressive program that systematically restores your range of motion. The result is not just increased flexibility, but improved balance, better posture, reduced injury risk, and greater ease in your daily activities.',
    ],
    whatToExpect: [
      'Functional movement screening to identify specific areas of restriction and imbalance',
      'Joint-by-joint assessment to determine which joints are restricted and which are compensating',
      'Chiropractic adjustments to restore proper joint mechanics in restricted areas',
      'A personalized stretching and mobility program progressing from gentle to more advanced',
      'Movement pattern correction to prevent compensatory habits from returning',
      'Regular reassessment to track range-of-motion improvements objectively',
    ],
    benefits: [
      'Restored range of motion in stiff and restricted joints',
      'Reduced risk of injuries during exercise and daily activities',
      'Improved balance, coordination, and functional movement',
      'Less pain and stiffness from sitting, standing, or repetitive motions',
      'Better athletic performance through optimized movement mechanics',
    ],
    imagePath: '/services/headache-migraine-relief.png',
    faqs: [
      {
        question: 'Why am I losing flexibility as I age?',
        answer:
          'Age-related flexibility loss is primarily caused by decreased water content in connective tissues, changes in muscle elasticity, and accumulated joint restrictions. However, much of this loss is preventable and reversible with consistent mobility work and chiropractic care that maintains proper joint mechanics.',
      },
      {
        question: 'Is stretching alone enough to improve mobility?',
        answer:
          'Not always. If a joint is misaligned or restricted, stretching the muscles around it won\'t fully restore mobility. Chiropractic adjustments restore the joint\'s ability to move through its full range, and then stretching helps the surrounding muscles adapt to that improved range. The combination is far more effective than either approach alone.',
      },
      {
        question: 'How often should I do mobility exercises?',
        answer:
          'For best results, we recommend daily mobility work for 10–15 minutes. Your personalized program will include exercises you can do at home, at your desk, or before/after workouts. Consistency matters more than intensity — a little every day is far better than a long session once a week.',
      },
      {
        question: 'Can mobility work help with chronic pain?',
        answer:
          'Absolutely. Many chronic pain conditions are exacerbated by restricted mobility and poor movement patterns. Restoring proper joint mechanics and muscle balance through mobility work often significantly reduces or eliminates chronic pain in the back, hips, shoulders, and neck.',
      },
    ],
  },
  {
    slug: 'pediatric-family-care',
    title: 'Pediatric & Family Care',
    icon: Heart,
    shortDescription:
      'Gentle chiropractic care for children and families, from newborns to seniors.',
    heroSubtitle:
      'Safe, gentle chiropractic care for every member of your family — from newborns to grandparents.',
    detailedDescription: [
      'Chiropractic care isn\'t just for adults with back pain. At Action Chiropractic, Dr. Bromberg provides gentle, age-appropriate care for patients of all ages. Children, teens, and seniors all benefit from proper spinal alignment — and the earlier healthy habits are established, the better the long-term outcomes.',
      'For children, common reasons to visit include growing pains, sports injuries, poor posture from backpacks and screens, and general wellness checkups. Pediatric adjustments use extremely gentle techniques with very little force — nothing like the adjustments you might imagine for adults. Many children actually enjoy their visits and look forward to them.',
      'For seniors, chiropractic care helps maintain mobility, reduce joint stiffness, improve balance, and manage age-related conditions like arthritis and spinal degeneration. Dr. Bromberg adapts his techniques for each patient\'s age, size, and condition — using gentle, low-force methods that are safe and effective for even the most sensitive patients. We believe whole-family wellness starts with proper spinal health at every stage of life.',
    ],
    whatToExpect: [
      'An age-appropriate intake and examination tailored to the patient\'s developmental stage',
      'Extremely gentle adjustments for children using fingertip pressure — no forceful manipulation',
      'Modified techniques for seniors that accommodate any existing conditions or sensitivities',
      'A comfortable, welcoming environment for patients of all ages',
      'Education for parents on posture, backpack ergonomics, screen time, and childhood wellness',
      'Family scheduling options so multiple family members can be seen during the same visit window',
    ],
    benefits: [
      'Early detection and correction of spinal issues before they become chronic',
      'Gentle, safe care that\'s appropriate for every age group',
      'Improved posture and reduced growing pains in children and teens',
      'Better mobility, balance, and quality of life for senior patients',
      'A family-centered approach that makes wellness a shared priority',
    ],
    imagePath: '/services/prenatal-chiropractic.png',
    faqs: [
      {
        question: 'Is chiropractic care safe for children?',
        answer:
          'Yes. Pediatric chiropractic care is very safe when performed by a trained practitioner. The adjustments used for children are extremely gentle — often using no more pressure than you\'d use to test the ripeness of a tomato. The International Chiropractic Pediatric Association provides specialized training that Dr. Bromberg has completed.',
      },
      {
        question: 'At what age can a child start seeing a chiropractor?',
        answer:
          'Children can benefit from chiropractic care at any age, including infancy. Newborn adjustments are incredibly gentle and focus on ensuring proper spinal development after the birth process. Many parents bring their children in for wellness checks starting in the first few weeks of life.',
      },
      {
        question: 'What conditions in children does chiropractic help with?',
        answer:
          'Common childhood conditions we address include colic, ear infections, growing pains, poor posture, sports injuries, headaches, and general wellness. While chiropractic care doesn\'t "treat" these conditions directly, removing spinal nerve interference allows the body to function and heal more effectively.',
      },
      {
        question: 'Is chiropractic care appropriate for elderly patients?',
        answer:
          'Absolutely. Seniors often benefit greatly from chiropractic care. We use gentle, low-force techniques that are safe for patients with osteoporosis, arthritis, or other age-related conditions. Regular care helps maintain mobility, reduce fall risk, manage pain, and improve overall quality of life.',
      },
    ],
  },
];
