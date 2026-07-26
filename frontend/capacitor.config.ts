import { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.finwatch.app',
  appName: 'FinWatch',
  webDir: 'dist',
  server: {
    androidScheme: 'https',
    cleartext: true,
    url: 'http://10.0.2.2:8000',
  },
  plugins: {
    LocalNotifications: {
      smallIcon: 'ic_notification',
      iconColor: '#3b82f6',
    },
  },
};

export default config;
