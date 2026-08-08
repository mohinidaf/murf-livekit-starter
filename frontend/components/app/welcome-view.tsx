'use client';

import { Button } from '@/components/ui/button';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
}: WelcomeViewProps) => {
  return (
    <div className="min-h-screen w-full bg-slate-950 text-white flex items-center justify-center px-6">
      <div className="max-w-6xl w-full grid lg:grid-cols-2 gap-16 items-center">

        {/* Left side */}
        <div>
          <div className="inline-flex px-4 py-2 rounded-full bg-emerald-500/20 text-emerald-400 text-sm">
            <span className="mr-2">●</span>
            AI Financial Voice Assistant
          </div>

          <h1 className="text-6xl font-bold mt-6">
            FinAssist
          </h1>

          <p className="mt-6 text-xl text-slate-300 leading-relaxed">
            Your intelligent voice assistant for Banking, UPI, Loans,
            Credit Cards, Insurance and Digital Payments.
          </p>

          <div className="grid grid-cols-2 gap-4 mt-10">
            <div className="bg-slate-800 rounded-xl p-4">
              Credit &amp; Debit Cards
            </div>

            <div className="bg-slate-800 rounded-xl p-4">
              UPI Payments
            </div>

            <div className="bg-slate-800 rounded-xl p-4">
              Banking &amp; Loans
            </div>

            <div className="bg-slate-800 rounded-xl p-4">
              Fraud Protection
            </div>
          </div>
        </div>

        {/* Right side */}
        <div className="flex flex-col items-center">

          <div className="w-44 h-44 rounded-full bg-emerald-500/20 border border-emerald-400 flex items-center justify-center animate-pulse">
            <div className="w-24 h-24 rounded-full bg-emerald-400" />
          </div>

          <p className="mt-8 text-xl font-medium">
            Ready to talk with FinAssist
          </p>

          <p className="mt-2 text-slate-400">
            Your AI financial voice assistant
          </p>

          <Button
            size="lg"
            onClick={onStartCall}
            className="mt-8 rounded-full px-12 py-7 text-lg"
          >
            🎤 {startButtonText}
          </Button>

        </div>
      </div>
    </div>
  );
};