import '../styles/globals.css';
import '../styles/auth.css';
import type { AppProps } from 'next/app';
import type { NextPage } from 'next';
import type { ReactElement, ReactNode } from 'react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import AiBubble from '../components/AiBubble';

import AiConcierge from '../components/AiConcierge';
import ScrollToTop from '../components/ScrollToTop';

export type NextPageWithLayout<P = {}, IP = P> = NextPage<P, IP> & {
  getLayout?: (page: ReactElement) => ReactNode;
};

type AppPropsWithLayout = AppProps & {
  Component: NextPageWithLayout;
};

export default function App({ Component, pageProps }: AppPropsWithLayout) {
  // If the page defines its own layout (e.g. login, register), use it
  if (Component.getLayout) {
    return Component.getLayout(<Component {...pageProps} />);
  }

  // Default layout
  return (
    <div className="page-shell-wrapper">
      <Navbar />
      <main className="main-site-content">
        <Component {...pageProps} />
      </main>
      <Footer />
      <AiConcierge />
      <ScrollToTop />
    </div>
  );
}
