from django.core.management.base import BaseCommand
from language_academy.models import World, Chapter, Lesson, LessonContent


class Command(BaseCommand):
    help = 'Initialize worlds, chapters, and lessons for Language Academy'

    def handle(self, *args, **options):

        airport_world = World.objects.create(
            name='Airport',
            name_fa='فرودگاه',
            description='Learn essential English for traveling through airports - from check-in to boarding and handling emergencies.',
            difficulty_level='A1',
            order=1,
            xp_reward=500,
            coin_reward=100,
            is_published=True
        )
        self.stdout.write(self.style.SUCCESS(f'Created world: {airport_world.name}'))


        chapters_data = [
            {'name': 'Travel Documents', 'order': 1,
             'description': 'Learn about passports, visas, and boarding passes'},
            {'name': 'Check-In', 'order': 2, 'description': 'Learn how to check in for your flight'},
            {'name': 'Security Check', 'order': 3,
             'description': 'Learn security checkpoint vocabulary and procedures'},
            {'name': 'Boarding', 'order': 4, 'description': 'Learn boarding announcements and procedures'},
            {'name': 'Immigration', 'order': 5, 'description': 'Learn immigration officer questions and answers'},
            {'name': 'Lost Luggage', 'order': 6, 'description': 'Learn how to report lost luggage'},
            {'name': 'Airport Emergencies', 'order': 7, 'description': 'Learn emergency phrases and situations'},
        ]

        for ch_data in chapters_data:
            chapter = Chapter.objects.create(
                world=airport_world,
                name=ch_data['name'],
                name_fa='',
                description=ch_data['description'],
                order=ch_data['order'],
                xp_reward=100,
                coin_reward=20,
                passing_score=70,
                is_published=True
            )
            self.stdout.write(f'  Created chapter: {chapter.name}')


            lesson = Lesson.objects.create(
                chapter=chapter,
                name=f'Introduction to {chapter.name}',
                name_fa='',
                lesson_type='mixed',
                order=1,
                xp_reward=50,
                coin_reward=10,
                is_published=True
            )


            LessonContent.objects.create(
                lesson=lesson,
                introduction=f'Welcome to {chapter.name}! In this lesson, you will learn important vocabulary and phrases.',
                learning_objectives=['Learn key vocabulary', 'Practice dialogue', 'Complete quiz'],
                grammar_notes='Pay attention to the present simple tense.',
                example_sentences=['Example sentence 1', 'Example sentence 2'],
                summary=f'You have completed the introduction to {chapter.name}.',
                key_takeaways=['Key point 1', 'Key point 2']
            )
            self.stdout.write(f'    Created lesson: {lesson.name}')

        self.stdout.write(self.style.SUCCESS('\n✅ All worlds and chapters created successfully!'))
