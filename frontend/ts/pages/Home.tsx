import { Link } from "@inertiajs/react";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-100 p-4">
      <h1 className="text-4xl font-bold text-gray-800">Welcome to the Home Page</h1>
      <p className="mt-4 text-lg text-gray-600">
        This is the main landing page of the application.
      </p>
      <div>
        <Button className="mt-6">
         <Link href="/feeds">
          Get Started
         </Link>
        </Button>
      </div>
    </div>
  );
}