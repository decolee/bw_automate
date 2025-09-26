import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  CheckCircle, 
  AlertCircle, 
  AlertTriangle, 
  Info, 
  X 
} from 'lucide-react';

const Toast = ({ message, type = 'info', onClose, duration = 5000 }) => {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        setIsVisible(false);
        setTimeout(onClose, 300); // Wait for exit animation
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);

  const handleClose = () => {
    setIsVisible(false);
    setTimeout(onClose, 300);
  };

  const typeConfig = {
    success: {
      icon: CheckCircle,
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200',
      iconColor: 'text-green-600',
      textColor: 'text-green-800'
    },
    error: {
      icon: AlertCircle,
      bgColor: 'bg-red-50',
      borderColor: 'border-red-200',
      iconColor: 'text-red-600',
      textColor: 'text-red-800'
    },
    warning: {
      icon: AlertTriangle,
      bgColor: 'bg-yellow-50',
      borderColor: 'border-yellow-200',
      iconColor: 'text-yellow-600',
      textColor: 'text-yellow-800'
    },
    info: {
      icon: Info,
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
      iconColor: 'text-blue-600',
      textColor: 'text-blue-800'
    }
  };

  const config = typeConfig[type] || typeConfig.info;
  const Icon = config.icon;

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, y: -50, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -50, scale: 0.95 }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
          className={`
            ${config.bgColor} ${config.borderColor} ${config.textColor}
            border rounded-xl shadow-apple backdrop-blur-sm
            p-4 min-w-80 max-w-md
          `}
        >
          <div className="flex items-start space-x-3">
            <Icon size={20} className={`${config.iconColor} flex-shrink-0 mt-0.5`} />
            
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium leading-relaxed">
                {message}
              </p>
            </div>
            
            <button
              onClick={handleClose}
              className={`
                ${config.iconColor} hover:opacity-70 flex-shrink-0 mt-0.5
                transition-opacity duration-200
              `}
            >
              <X size={16} />
            </button>
          </div>

          {/* Progress bar for timed toasts */}
          {duration > 0 && (
            <motion.div
              className="mt-3 h-1 bg-black bg-opacity-10 rounded-full overflow-hidden"
            >
              <motion.div
                className={`h-full ${config.iconColor.replace('text-', 'bg-')} opacity-60`}
                initial={{ width: '100%' }}
                animate={{ width: '0%' }}
                transition={{ duration: duration / 1000, ease: 'linear' }}
              />
            </motion.div>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default Toast;