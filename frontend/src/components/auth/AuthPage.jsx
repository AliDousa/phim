import React, { useState } from 'react';
import LoginForm from './LoginForm';
import RegisterForm from './RegisterForm';
import { Brain, Globe, Shield, Zap } from 'lucide-react';

const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);

  const features = [
    {
      icon: Brain,
      title: 'Advanced Analytics',
      description: 'Leverage machine learning for epidemiological modeling and forecasting'
    },
    {
      icon: Globe,
      title: 'Global Data',
      description: 'Access and analyze public health data from around the world'
    },
    {
      icon: Shield,
      title: 'Secure Platform',
      description: 'Enterprise-grade security for sensitive health information'
    },
    {
      icon: Zap,
      title: 'Real-time Insights',
      description: 'Get instant results from complex simulations and analyses'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-2 gap-12 items-center min-h-screen">
          {/* Left side - Branding and features */}
          <div className="space-y-8">
            <div className="text-center lg:text-left">
              <h1 className="text-4xl lg:text-5xl font-bold text-gray-900 dark:text-white mb-4">
                Public Health
                <span className="block text-blue-600 dark:text-blue-400">
                  Intelligence Platform
                </span>
              </h1>
              <p className="text-xl text-gray-600 dark:text-gray-300 max-w-md">
                Advanced tools for epidemiological modeling, data analysis, and public health insights.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {features.map((feature, index) => (
                <div key={index} className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    <feature.icon className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">
                      {feature.title}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-300">
                      {feature.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            <div className="pt-8 border-t border-gray-200 dark:border-gray-700">
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Trusted by researchers and health organizations worldwide for critical public health decision-making.
              </p>
            </div>
          </div>

          {/* Right side - Auth forms */}
          <div className="flex items-center justify-center">
            {isLogin ? (
              <LoginForm onSwitchToRegister={() => setIsLogin(false)} />
            ) : (
              <RegisterForm onSwitchToLogin={() => setIsLogin(true)} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;