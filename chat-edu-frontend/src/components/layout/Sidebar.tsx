import { useAuth } from '@/contexts/AuthContext';
import { useCourse } from '@/contexts/CourseContext';
import { ScrollArea } from '@/components/ui/scroll-area';
import { BookOpen } from 'lucide-react';
import { cn } from '@/lib/utils';

export const Sidebar = () => {
  const { courses } = useAuth();
  const { selectedCourse, setSelectedCourse } = useCourse();

  return (
    <aside className="w-64 border-r bg-card h-[calc(100vh-4rem)]">
      <div className="p-4 border-b">
        <h2 className="font-semibold text-foreground">Meus Cursos</h2>
        <p className="text-xs text-muted-foreground mt-1">
          {courses.length} {courses.length === 1 ? 'curso' : 'cursos'}
        </p>
      </div>
      
      <ScrollArea className="h-[calc(100vh-8rem)]">
        <div className="p-2 space-y-1">
          {courses.map((course) => (
            <button
              key={course.id}
              onClick={() => setSelectedCourse(course)}
              className={cn(
                "w-full text-left p-3 rounded-lg transition-all hover:bg-muted/50",
                selectedCourse?.id === course.id
                  ? "bg-gradient-to-r from-primary/10 to-secondary/10 border border-primary/20"
                  : "hover:bg-muted"
              )}
            >
              <div className="flex items-start gap-3">
                <div className={cn(
                  "w-8 h-8 rounded-md flex items-center justify-center shrink-0",
                  selectedCourse?.id === course.id
                    ? "bg-gradient-to-br from-primary to-secondary"
                    : "bg-muted"
                )}>
                  <BookOpen className={cn(
                    "w-4 h-4",
                    selectedCourse?.id === course.id
                      ? "text-primary-foreground"
                      : "text-muted-foreground"
                  )} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className={cn(
                    "text-sm font-medium truncate",
                    selectedCourse?.id === course.id
                      ? "text-primary"
                      : "text-foreground"
                  )}>
                    {course.nome}
                  </p>
                  {course.descricao && (
                    <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                      {course.descricao}
                    </p>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>
      </ScrollArea>
    </aside>
  );
};
