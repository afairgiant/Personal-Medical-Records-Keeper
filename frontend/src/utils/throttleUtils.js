/**
 * Throttling Utilities for Activity Tracking
 * Centralized throttling logic with error handling and safety measures
 */

/**
 * Creates a throttled function with built-in error handling and safety measures
 * @param {Function} func - The function to throttle
 * @param {number} delay - The throttle delay in milliseconds
 * @param {Object} options - Throttle options
 * @param {boolean} options.leading - Execute on leading edge (default: true)
 * @param {boolean} options.trailing - Execute on trailing edge (default: false)
 * @param {Function} options.onError - Error handler function
 * @param {string} options.debugName - Name for debugging purposes
 * @returns {Function} Throttled function with cleanup method
 */
export function createSafeThrottle(func, delay, options = {}) {
  const {
    leading = true,
    trailing = false,
    onError = null,
    debugName = 'throttled-function'
  } = options;

  let timeoutId = null;
  let lastCallTime = 0;
  let lastArgs = null;
  let isDestroyed = false;

  const throttledFunction = function(...args) {
    // Prevent execution if throttle has been destroyed
    if (isDestroyed) {
      if (process.env.NODE_ENV === 'development') {
        console.warn(`Attempted to call destroyed throttle: ${debugName}`);
      }
      return;
    }

    const currentTime = Date.now();
    const timeSinceLastCall = currentTime - lastCallTime;
    
    lastArgs = args;

    // If enough time has passed, execute immediately (leading edge)
    if (leading && timeSinceLastCall >= delay) {
      if (timeoutId) {
        clearTimeout(timeoutId);
        timeoutId = null;
      }
      return safeExecute();
    }

    // If trailing edge is enabled and we don't have a pending timeout
    if (trailing && !timeoutId) {
      const remainingTime = delay - timeSinceLastCall;
      timeoutId = setTimeout(() => {
        timeoutId = null;
        if (!isDestroyed) {
          safeExecute();
        }
      }, Math.max(0, remainingTime));
    }
  };

  // Add cleanup method
  throttledFunction.cleanup = () => {
    isDestroyed = true;
    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }
    lastArgs = null;
  };

  // Add method to check if throttle is active
  throttledFunction.isPending = () => timeoutId !== null;
  
  // Helper function to safely execute the original function (moved to outer scope)
  const safeExecute = () => {
    if (isDestroyed) return;
    
    try {
      lastCallTime = Date.now();
      return func.apply(this, lastArgs);
    } catch (error) {
      if (onError) {
        try {
          onError(error, debugName, lastArgs);
        } catch (handlerError) {
          console.error(`Error in throttle error handler for ${debugName}:`, handlerError);
        }
      } else {
        console.error(`Error in throttled function ${debugName}:`, error);
      }
    }
  };

  // Add method to flush pending execution
  throttledFunction.flush = () => {
    if (timeoutId && !isDestroyed) {
      clearTimeout(timeoutId);
      timeoutId = null;
      safeExecute();
    }
  };

  // Add method to check if destroyed
  throttledFunction.isDestroyed = () => isDestroyed;

  return throttledFunction;
}

/**
 * Creates a throttled function specifically for activity tracking
 * @param {Function} activityFunc - The activity function to throttle
 * @param {number} delay - The throttle delay in milliseconds
 * @param {string} activityType - Type of activity (for debugging)
 * @returns {Function} Throttled activity function
 */
export function createActivityThrottle(activityFunc, delay, activityType) {
  return createSafeThrottle(activityFunc, delay, {
    leading: true,
    trailing: false,
    debugName: `activity-${activityType}`,
    onError: (error, debugName, args) => {
      // Log activity tracking errors without exposing sensitive data
      console.error(`Activity tracking error in ${debugName}:`, {
        error: error.message,
        type: activityType,
        timestamp: new Date().toISOString(),
        // Don't log args as they might contain sensitive event data
      });
    }
  });
}

/**
 * Race condition safe wrapper for async functions
 * Prevents multiple concurrent executions of the same async function
 * @param {Function} asyncFunc - The async function to wrap
 * @param {string} debugName - Name for debugging purposes
 * @returns {Function} Race-safe async function
 */
export function createRaceSafeWrapper(asyncFunc, debugName = 'async-function') {
  let pendingPromise = null;
  let isDestroyed = false;

  const wrapper = async function(...args) {
    if (isDestroyed) {
      throw new Error(`Attempted to call destroyed race-safe wrapper: ${debugName}`);
    }

    // If there's already a pending execution, return that promise
    if (pendingPromise) {
      return pendingPromise;
    }

    try {
      pendingPromise = asyncFunc.apply(this, args);
      const result = await pendingPromise;
      return result;
    } catch (error) {
      throw error;
    } finally {
      pendingPromise = null;
    }
  };

  wrapper.cleanup = () => {
    isDestroyed = true;
    pendingPromise = null;
  };

  wrapper.isPending = () => pendingPromise !== null;
  wrapper.isDestroyed = () => isDestroyed;

  return wrapper;
}

/**
 * Retry wrapper for functions that might fail
 * @param {Function} func - Function to wrap with retry logic
 * @param {number} maxRetries - Maximum number of retries
 * @param {number} baseDelay - Base delay between retries in milliseconds
 * @param {string} debugName - Name for debugging
 * @returns {Function} Function with retry logic
 */
export function createRetryWrapper(func, maxRetries = 3, baseDelay = 1000, debugName = 'retry-function') {
  return async function(...args) {
    let lastError;
    
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await func.apply(this, args);
      } catch (error) {
        lastError = error;
        
        if (attempt === maxRetries) {
          console.error(`${debugName} failed after ${maxRetries} retries:`, error);
          throw error;
        }
        
        // Exponential backoff with jitter
        const delay = baseDelay * Math.pow(2, attempt) + Math.random() * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
        
        if (process.env.NODE_ENV === 'development') {
          console.warn(`${debugName} retry ${attempt + 1}/${maxRetries} after error:`, error.message);
        }
      }
    }
    
    throw lastError;
  };
}

/**
 * Creates a cleanup manager for multiple throttled functions
 * @returns {Object} Cleanup manager with add, cleanup, and cleanupAll methods
 */
export function createThrottleCleanupManager() {
  const throttles = new Set();
  let isDestroyed = false;

  return {
    add(throttledFunction) {
      if (isDestroyed) {
        throw new Error('Cannot add to destroyed cleanup manager');
      }
      throttles.add(throttledFunction);
    },

    remove(throttledFunction) {
      throttles.delete(throttledFunction);
    },

    cleanupAll() {
      for (const throttle of throttles) {
        try {
          if (throttle.cleanup) {
            throttle.cleanup();
          }
        } catch (error) {
          console.error('Error cleaning up throttle:', error);
        }
      }
      throttles.clear();
      isDestroyed = true;
    },
    
    get isDestroyed() {
      return isDestroyed;
    },

    size() {
      return throttles.size;
    },

    isDestroyed() {
      return isDestroyed;
    }
  };
}