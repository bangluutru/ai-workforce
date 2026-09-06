export interface ProductItem {
  id: string;
  name: string;
  price: number;
  originalPrice?: number;
  image?: string;
  badge?: string;
  variant?: string;
  features?: string[];
}

export interface TestimonialItem {
  id: string;
  author: string;
  role?: string;
  avatar?: string;
  rating: number;
  comment: string;
}

export interface BenefitItem {
  id: string;
  title: string;
  description: string;
  icon?: string;
}

export interface FaqItem {
  question: string;
  answer: string;
}
