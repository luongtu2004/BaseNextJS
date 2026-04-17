import Header from "@/components/Header";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />
      <main className="flex-grow flex flex-col items-center justify-center p-8 sm:p-20">
        <div className="max-w-2xl w-full bg-white rounded-2xl shadow-sm border border-gray-100 p-12 text-center">
          <h1 className="text-4xl font-extrabold text-gray-900 mb-4">
            Welcome to your new project
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            The foundation is ready. You have a clean Next.js frontend and a Node.js backend structure.
          </p>
          <div className="flex gap-4 justify-center">
            <div className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors cursor-pointer">
              Get Started
            </div>
            <div className="px-6 py-3 bg-white text-gray-700 border border-gray-200 rounded-lg font-semibold hover:bg-gray-50 transition-colors cursor-pointer">
              Documentation
            </div>
          </div>
        </div>
      </main>
      
      <footer className="py-8 text-center text-gray-400 text-sm border-t border-gray-100 bg-white">
        © 2024 Your Brand. All rights reserved.
      </footer>
    </div>
  );
}
