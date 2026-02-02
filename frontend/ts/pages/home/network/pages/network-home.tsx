import React, { useState } from "react";
import {
  Search,
  MapPin,
  Briefcase,
  BookmarkPlus,
  MessageSquare,
  UserPlus,
  MoreVertical,
  Users,
  Building2,
  Calendar,
  ChevronDown,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";

// Types
type UserRole = "student" | "alumni";

interface Member {
  id: string;
  name: string;
  position: string;
  company: string;
  promo: string;
  location: string;
  avatar: string;
  isMentor?: boolean;
  isAvailable?: boolean;
}

interface Group {
  id: string;
  name: string;
  description: string;
  memberCount: number;
  image: string;
  isJoined: boolean;
}

interface Organization {
  id: string;
  name: string;
  sector: string;
  location: string;
  logo: string;
  alumniCount: number;
  featured?: boolean;
}

interface NetworkPageProps {
  userRole: UserRole;
  members?: Member[];
  groups?: Group[];
  organizations?: Organization[];
}

const NetworkPage: React.FC<NetworkPageProps> = ({
  userRole = "alumni",
  members = [],
  groups = [],
  organizations = [],
}) => {
  const [activeTab, setActiveTab] = useState("members");
  const [searchQuery, setSearchQuery] = useState("");

  // Mock data for demonstration
  const mockMembers: Member[] =
    members.length > 0
      ? members
      : [
          {
            id: "1",
            name: "Marie Curie",
            position: "Senior Engineer",
            company: "Google",
            promo: "Promo 2018",
            location: "Paris, France",
            avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Marie",
            isMentor: true,
            isAvailable: true,
          },
          {
            id: "2",
            name: "Jean Dupont",
            position: "Data Scientist",
            company: "Microsoft",
            promo: "Promo 2020",
            location: "Lyon, France",
            avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Jean",
            isMentor: false,
          },
          {
            id: "3",
            name: "Sarah Johnson",
            position: "Product Manager",
            company: "Amazon",
            promo: "Promo 2019",
            location: "London, UK",
            avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Sarah",
            isMentor: true,
            isAvailable: true,
          },
        ];

  const mockGroups: Group[] =
    groups.length > 0
      ? groups
      : [
          {
            id: "1",
            name: "Club Robotique",
            description: "Passionate about robotics and automation",
            memberCount: 124,
            image:
              "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=400",
            isJoined: false,
          },
          {
            id: "2",
            name: "Alumni Paris",
            description: "Network of Paris-based alumni",
            memberCount: 342,
            image:
              "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=400",
            isJoined: true,
          },
          {
            id: "3",
            name: "Data Science Hub",
            description: "Share insights and projects in data science",
            memberCount: 287,
            image:
              "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400",
            isJoined: false,
          },
        ];

  const mockOrganizations: Organization[] =
    organizations.length > 0
      ? organizations
      : [
          {
            id: "1",
            name: "TotalEnergies",
            sector: "Energy • Tech",
            location: "Paris, France",
            logo: "https://logo.clearbit.com/totalenergies.com",
            alumniCount: 45,
            featured: true,
          },
          {
            id: "2",
            name: "Airbus",
            sector: "Aerospace • Defense",
            location: "Toulouse, France",
            logo: "https://logo.clearbit.com/airbus.com",
            alumniCount: 32,
          },
          {
            id: "3",
            name: "Schlumberger",
            sector: "Energy • Tech",
            location: "Houston, USA",
            logo: "https://logo.clearbit.com/slb.com",
            alumniCount: 28,
          },
        ];

  return (
    <div className="space-y-6">
      {/* Hero Section - Mentorship CTA */}
      <Card className="overflow-hidden md:mt-4">
        <div className="flex flex-col md:flex-row">
          <div className="md:w-1/3 h-64 md:h-auto bg-muted relative overflow-hidden">
            <img
              src="https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=800"
              alt="Mentorship collaboration"
              className="w-full h-full object-cover"
            />
            <div className="absolute inset-0 bg-primary/10" />
          </div>
          <div className="p-8 md:w-2/3 flex flex-col justify-center">
            <Badge
              variant="secondary"
              className="w-fit mb-3 bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-200 border-0"
            >
              MENTORSHIP PROGRAM
            </Badge>
            <h1 className="text-3xl md:text-4xl font-bold mb-4 tracking-tight">
              Accelerate your career through Mentorship
            </h1>
            <p className="text-muted-foreground text-lg mb-8 max-w-2xl">
              Connect with 5,000+ Alumni and students to share knowledge, gain
              insights, and grow together in the engineering field.
            </p>
            <div className="flex flex-wrap gap-4">
              {userRole === "student" ? (
                <>
                  <Button size="lg" className="gap-2">
                    <Search className="h-4 w-4" />
                    Find a Mentor
                  </Button>
                  <Button size="lg" variant="outline" className="gap-2">
                    <Users className="h-4 w-4" />
                    Browse Mentors
                  </Button>
                </>
              ) : (
                <>
                  <Button size="lg" variant="outline" className="gap-2">
                    <UserPlus className="h-4 w-4" />
                    Become a Mentor
                  </Button>
                  <Button size="lg" className="gap-2">
                    <Search className="h-4 w-4" />
                    Find a Mentee
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </Card>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Sidebar - Filters */}
        <aside className="hidden lg:block lg:col-span-3 space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-3">
              <CardTitle className="text-base">Filters</CardTitle>
              <Button
                variant="ghost"
                size="sm"
                className="text-xs text-primary h-auto p-0 hover:underline"
              >
                Clear all
              </Button>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Search by name */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Search by name
                </label>
                <Input
                  placeholder="e.g. Jean Dupont"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>

              {/* Promo Filter */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Promotion
                </label>
                <Select>
                  <SelectTrigger>
                    <SelectValue placeholder="All years" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All years</SelectItem>
                    <SelectItem value="2024">2024</SelectItem>
                    <SelectItem value="2023">2023</SelectItem>
                    <SelectItem value="2022">2022</SelectItem>
                    <SelectItem value="2021">2021</SelectItem>
                    <SelectItem value="2020">2020</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Speciality Filter */}
              <div className="space-y-3">
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Speciality
                </label>
                <div className="space-y-2">
                  {[
                    "Computer Science",
                    "Civil Engineering",
                    "Mechanical Engineering",
                    "Electrical Engineering",
                  ].map((spec) => (
                    <div key={spec} className="flex items-center space-x-2">
                      <Checkbox id={spec} />
                      <label
                        htmlFor={spec}
                        className="text-sm leading-none cursor-pointer"
                      >
                        {spec}
                      </label>
                    </div>
                  ))}
                </div>
              </div>

              {/* Location Filter */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  Location
                </label>
                <Select>
                  <SelectTrigger>
                    <SelectValue placeholder="All locations" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All locations</SelectItem>
                    <SelectItem value="paris">Paris, France</SelectItem>
                    <SelectItem value="lyon">Lyon, France</SelectItem>
                    <SelectItem value="london">London, UK</SelectItem>
                    <SelectItem value="berlin">Berlin, Germany</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Mentor Availability */}
              {activeTab === "members" && (
                <div className="flex items-center space-x-2">
                  <Checkbox id="mentors-only" />
                  <label
                    htmlFor="mentors-only"
                    className="text-sm leading-none cursor-pointer"
                  >
                    Available mentors only
                  </label>
                </div>
              )}
            </CardContent>
          </Card>
        </aside>

        {/* Main Content Area */}
        <main className="lg:col-span-6">
          <Tabs
            value={activeTab}
            onValueChange={setActiveTab}
            className="space-y-6"
          >
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="members" className="gap-2">
                <Users className="h-4 w-4" />
                Members
              </TabsTrigger>
              <TabsTrigger value="groups" className="gap-2">
                <Users className="h-4 w-4" />
                Groups
              </TabsTrigger>
              <TabsTrigger value="organizations" className="gap-2">
                <Building2 className="h-4 w-4" />
                Organizations
              </TabsTrigger>
            </TabsList>

            {/* Members Tab */}
            <TabsContent value="members" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {mockMembers.map((member) => (
                  <Card
                    key={member.id}
                    className="hover:border-primary/50 transition-all"
                  >
                    <CardContent className="p-6">
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-start gap-4">
                          <Avatar className="h-16 w-16">
                            <AvatarImage
                              src={member.avatar}
                              alt={member.name}
                            />
                            <AvatarFallback>
                              {member.name
                                .split(" ")
                                .map((n) => n[0])
                                .join("")}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <h3 className="font-semibold text-lg mb-1">
                              {member.name}
                            </h3>
                            <p className="text-sm text-muted-foreground flex items-center gap-1">
                              <Briefcase className="h-3 w-3" />
                              {member.position} @ {member.company}
                            </p>
                            <p className="text-xs text-muted-foreground mt-1">
                              {member.promo}
                            </p>
                          </div>
                        </div>
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </div>

                      <div className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
                        <MapPin className="h-4 w-4" />
                        {member.location}
                      </div>

                      {member.isMentor && (
                        <Badge
                          variant="outline"
                          className="mb-4 border-green-500/50 text-green-600 dark:text-green-400"
                        >
                          <span className="mr-1">✓</span> Mentor Available
                        </Badge>
                      )}

                      <div className="flex gap-2">
                        <Button className="flex-1 gap-2">
                          <MessageSquare className="h-4 w-4" />
                          Message
                        </Button>
                        <Button variant="outline" size="icon">
                          <BookmarkPlus className="h-4 w-4" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
              <Button variant="ghost" className="w-full gap-2 text-primary">
                Load more members
                <ChevronDown className="h-4 w-4" />
              </Button>
            </TabsContent>

            {/* Groups Tab */}
            <TabsContent value="groups" className="space-y-4">
              <div className="space-y-4">
                {mockGroups.map((group) => (
                  <Card
                    key={group.id}
                    className="hover:border-primary/50 transition-all"
                  >
                    <CardContent className="p-6">
                      <div className="flex gap-4">
                        <div className="h-20 w-20 rounded-lg overflow-hidden flex-shrink-0 bg-muted">
                          <img
                            src={group.image}
                            alt={group.name}
                            className="w-full h-full object-cover"
                          />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <h3 className="font-semibold text-lg mb-1">
                                {group.name}
                              </h3>
                              <p className="text-sm text-muted-foreground mb-2">
                                {group.description}
                              </p>
                              <p className="text-xs text-muted-foreground flex items-center gap-1">
                                <Users className="h-3 w-3" />
                                {group.memberCount} members
                              </p>
                            </div>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                            >
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </div>
                          <div className="flex gap-2 mt-4">
                            {group.isJoined ? (
                              <Button variant="outline" className="flex-1">
                                Joined
                              </Button>
                            ) : (
                              <Button className="flex-1">Join Group</Button>
                            )}
                            <Button variant="outline">View</Button>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
              <Button variant="ghost" className="w-full gap-2 text-primary">
                Load more groups
                <ChevronDown className="h-4 w-4" />
              </Button>
            </TabsContent>

            {/* Organizations Tab */}
            <TabsContent value="organizations" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {mockOrganizations.map((org) => (
                  <Card
                    key={org.id}
                    className="hover:border-primary/50 transition-all"
                  >
                    <CardContent className="p-6">
                      <div className="flex items-start justify-between mb-4">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 ml-auto"
                        >
                          <BookmarkPlus className="h-4 w-4" />
                        </Button>
                      </div>

                      <div className="flex items-start gap-4 mb-4">
                        <div className="h-14 w-14 rounded-lg bg-white dark:bg-card p-2 flex items-center justify-center border">
                          <img
                            src={org.logo}
                            alt={`${org.name} logo`}
                            className="w-full h-full object-contain"
                          />
                        </div>
                        <div>
                          <h3 className="font-semibold text-lg mb-1">
                            {org.name}
                          </h3>
                          <p className="text-sm text-muted-foreground">
                            {org.sector}
                          </p>
                          <p className="text-xs text-muted-foreground flex items-center gap-1 mt-1">
                            <MapPin className="h-3 w-3" />
                            {org.location}
                          </p>
                        </div>
                      </div>

                      {org.featured && (
                        <Badge
                          variant="secondary"
                          className="mb-4 bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20"
                        >
                          <Calendar className="h-3 w-3 mr-1" />
                          Speaking at next event
                        </Badge>
                      )}

                      <div className="border-t pt-4 space-y-4">
                        <div className="flex items-center gap-2">
                          <div className="flex -space-x-2">
                            {[1, 2].map((i) => (
                              <Avatar
                                key={i}
                                className="h-6 w-6 border-2 border-background"
                              >
                                <AvatarImage
                                  src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${org.id}-${i}`}
                                />
                                <AvatarFallback>A</AvatarFallback>
                              </Avatar>
                            ))}
                          </div>
                          <span className="text-xs font-medium">
                            {org.alumniCount} alumni work here
                          </span>
                        </div>
                        <Button variant="outline" className="w-full">
                          View Page
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
              <Button variant="ghost" className="w-full gap-2 text-primary">
                Load more organizations
                <ChevronDown className="h-4 w-4" />
              </Button>
            </TabsContent>
          </Tabs>
        </main>

        {/* Right Sidebar - Suggestions */}
        <aside className="hidden lg:block lg:col-span-3 space-y-6">
          {/* Promo Card */}
          <Card className="bg-gradient-to-br from-primary/20 to-primary/5 border-primary/20 overflow-hidden">
            <CardContent className="p-6 relative">
              <div className="absolute -right-6 -top-6 h-24 w-24 bg-primary/20 rounded-full blur-xl" />
              <div className="relative space-y-4">
                <div className="flex items-start justify-between">
                  <div className="bg-background/50 p-2 rounded-lg">
                    <Calendar className="h-5 w-5 text-primary" />
                  </div>
                  <Badge className="bg-primary/10 text-primary border-0 text-[10px] uppercase font-bold">
                    Upcoming
                  </Badge>
                </div>
                <div>
                  <h3 className="font-bold text-lg mb-1">Annual Career Fair</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Meet 50+ top engineering companies in person.
                  </p>
                  <Button className="w-full">Register Now</Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Trending in Network */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">
                Trending in your network
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {[
                {
                  name: "Sarah M.",
                  role: "HR at Airbus",
                  avatar:
                    "https://api.dicebear.com/7.x/avataaars/svg?seed=Sarah",
                },
                {
                  name: "David K.",
                  role: "Senior Eng. at Tesla",
                  avatar:
                    "https://api.dicebear.com/7.x/avataaars/svg?seed=David",
                },
                {
                  name: "Emily R.",
                  role: "Recruiter at Google",
                  avatar:
                    "https://api.dicebear.com/7.x/avataaars/svg?seed=Emily",
                },
              ].map((person, idx) => (
                <div key={idx} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Avatar className="h-10 w-10">
                      <AvatarImage src={person.avatar} alt={person.name} />
                      <AvatarFallback>{person.name[0]}</AvatarFallback>
                    </Avatar>
                    <div>
                      <h4 className="text-sm font-semibold">{person.name}</h4>
                      <p className="text-xs text-muted-foreground">
                        {person.role}
                      </p>
                    </div>
                  </div>
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <UserPlus className="h-4 w-4" />
                  </Button>
                </div>
              ))}
              <Button
                variant="ghost"
                className="w-full text-xs text-muted-foreground hover:text-foreground"
              >
                View all recommendations
              </Button>
            </CardContent>
          </Card>

          {/* Footer Links */}
          <div className="flex flex-wrap gap-x-4 gap-y-2 px-2 text-xs text-muted-foreground">
            <a href="#" className="hover:underline">
              About
            </a>
            <a href="#" className="hover:underline">
              Accessibility
            </a>
            <a href="#" className="hover:underline">
              Help Center
            </a>
            <a href="#" className="hover:underline">
              Privacy & Terms
            </a>
            <p className="w-full mt-2">© 2023 ENSPM Hub Corporation</p>
          </div>
        </aside>
      </div>
    </div>
  );
};

export default NetworkPage;
