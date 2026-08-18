import math
import numpy as np
from functools import lru_cache

from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import TemplateView
from statistics import mean, median, mode, StatisticsError
import json
import re

from .forms import NumbersForm


def validate_positive_float(value, field_name, max_val=10000):
    if value is None or str(value).strip() == "":
        raise ValueError(f"فیلد {field_name} نمی‌تواند خالی باشد.")
    try:
        num = float(value)
        if num <= 0:
            raise ValueError(f"{field_name} باید بزرگتر از صفر باشد.")
        if num > max_val:
            raise ValueError(f"{field_name} خیلی بزرگ است (حداکثر {max_val}).")
        return num
    except ValueError:
        raise ValueError(f"مقدار {field_name} معتبر نیست.")


def math_products(request):
    return render(request, 'main-page.html')


class FactorialView(TemplateView):
    template_name = 'factorial-page.html'

    def post(self, request, *args, **kwargs):
        context = {'result': None, 'error': None, 'input_value': ''}
        user_input = request.POST.get('number', '').strip()
        context['input_value'] = user_input

        if not user_input:
            context['error'] = 'لطفاً یک عدد وارد کنید.'
        elif not user_input.isdigit():
            context['error'] = 'ورودی باید فقط شامل اعداد صحیح باشد.'
        else:
            number = int(user_input)
            if number > 30:
                context['error'] = 'محاسبه فاکتوریل برای عدد بالاتر از ۳۰ پشتیبانی نمی‌شود.'
            else:
                context['result'] = math.factorial(number)

        return self.render_to_response(context)


@lru_cache(maxsize=1000)
def is_prime_vectorized(n):
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False

    limit = int(np.sqrt(n))
    divisors = np.arange(5, limit + 1, 6)
    if np.any((n % divisors == 0) | (n % (divisors + 2) == 0)):
        return False
    return True


def get_divisors_numpy(n):
    if n <= 0:
        return []
    divisors = np.arange(1, n + 1)
    return divisors[n % divisors == 0].tolist()


def prime_calculator(request):
    result = None
    divisors = None
    error_message = None
    number = None

    if request.method == 'POST':
        try:
            number = int(request.POST.get('number', 0))

            if number > 10_000_000:
                error_message = "عدد وارد شده باید کمتر از 10 میلیون باشد."
            elif number <= 1:
                error_message = "عدد وارد شده نه اول است و نه مرکب."
            else:
                result = is_prime_vectorized(number)
                if not result:
                    divisors = get_divisors_numpy(number)
        except ValueError:
            error_message = "لطفاً یک عدد صحیح وارد کنید."

    return render(request, 'calculating-perimerter-area.html', {
        'result': result,
        'divisors': divisors,
        'error_message': error_message,
        'number': number
    })


from django.shortcuts import render
import math


def get_divisors(n):
    divisors = []
    i = 1
    while i * i <= n:
        if n % i == 0:
            divisors.append(i)
            if i != n // i:
                divisors.append(n // i)
        i += 1
    return sorted(divisors)


def gcd_lcm_view(request):
    if request.method == "POST":
        try:
            num1 = int(request.POST.get('num1', 0))
            num2 = int(request.POST.get('num2', 0))

            if num1 <= 0 or num2 <= 0:
                raise ValueError("اعداد باید مثبت باشند")


            gcd_result = math.gcd(num1, num2)


            lcm_result = (num1 * num2) // gcd_result


            divisors1 = get_divisors(num1) if num1 <= 10000 else []
            divisors2 = get_divisors(num2) if num2 <= 10000 else []

            context = {
                'num1': num1,
                'num2': num2,
                'divisors1': divisors1,
                'divisors2': divisors2,
                'gcd_result': gcd_result,
                'lcm_result': lcm_result,
                'show_result': True,
            }
        except (ValueError, TypeError, ZeroDivisionError):
            context = {'error': 'لطفاً اعداد معتبر و مثبت وارد کنید', 'show_result': False}
    else:
        context = {'show_result': False}

    return render(request, 'gcd_lcm_form.html', context)


import numpy as np
from django.shortcuts import render


def validate_positive_float(value, field_name):
    if value is None or value == '':
        raise ValueError(f"لطفاً مقدار {field_name} را وارد کنید.")

    try:
        num = float(value)
        if num <= 0:
            raise ValueError(f"مقدار {field_name} باید مثبت باشد.")
        return num
    except ValueError:
        raise ValueError(f"مقدار {field_name} نامعتبر است. لطفاً یک عدد وارد کنید.")


def pythagorean_triangle(request):
    result = error = None

    if request.method == "POST":
        mode = request.POST.get("mode")

        try:
            if mode == "two_sides":
                a = validate_positive_float(request.POST.get("a"), "ضلع a")
                b = validate_positive_float(request.POST.get("b"), "ضلع b")
                c = np.sqrt(a ** 2 + b ** 2)
                B = np.degrees(np.arctan(b / a))

            elif mode == "one_side_one_angle":
                a = validate_positive_float(request.POST.get("a_oa"), "ضلع")
                angle_B = float(request.POST.get("angle_oa"))
                if not (0 < angle_B < 90):
                    raise ValueError("زاویه باید بین ۰ تا ۹۰ باشد.")
                B = angle_B
                b = a * np.tan(np.radians(B))
                c = a / np.cos(np.radians(B))

            elif mode == "hypotenuse_and_leg":
                c = validate_positive_float(request.POST.get("c_hl"), "وتر")
                leg = validate_positive_float(request.POST.get("leg_hl"), "ضلع")
                if leg >= c:
                    raise ValueError("ضلع نمی‌تواند بزرگتر یا مساوی وتر باشد.")
                leg_name = request.POST.get("leg_name")
                if leg_name == "a":
                    a, b = leg, np.sqrt(c ** 2 - leg ** 2)
                else:
                    b, a = leg, np.sqrt(c ** 2 - leg ** 2)
                B = np.degrees(np.arctan(b / a))

            elif mode == "hypotenuse_and_angle":
                c = validate_positive_float(request.POST.get("c_ha"), "وتر")
                angle_B = float(request.POST.get("angle_ha"))
                if not (0 < angle_B < 90):
                    raise ValueError("زاویه باید بین ۰ تا ۹۰ باشد.")
                B = angle_B
                a = c * np.cos(np.radians(B))
                b = c * np.sin(np.radians(B))
            else:
                raise ValueError("حالت انتخابی نامعتبر است.")

            C = 90 - B


            scale = 200 / max(a, b)
            ax, ay = 20, 280
            bx, by = ax + a * scale, ay
            cx, cy = ax, ay - b * scale

            result = {
                'a': round(float(a), 2),
                'b': round(float(b), 2),
                'c': round(float(c), 2),
                'B': round(float(B), 2),
                'C': round(float(C), 2),
                'svg_points': f"{ax},{ay} {bx},{by} {cx},{cy}",
                'labels': {
                    'A': (ax - 10, ay + 10),
                    'B': (bx + 5, by + 15),
                    'C': (cx - 20, cy - 5)
                }
            }

        except ValueError as ve:
            error = str(ve)
        except Exception:
            error = "خطایی در پردازش ورودی‌ها رخ داده است."

    return render(request, "pythagorean.html", {"result": result, "error": error})


AREA_PERIMETER_SHAPES = {
    "مثلث": {
        "area": {
            "calculate": lambda d: (d["base"] * d["height"]) / 2,
            "formula": "مساحت مثلث = (قاعده × ارتفاع) ÷ ۲",
            "inputs": ["base", "height"]
        },
        "perimeter": {
            "calculate": lambda d: 3 * d["side"],
            "formula": "محیط مثلث متساوی الاضلاع = ۳ × ضلع",
            "inputs": ["side"]
        }
    },
    "مربع": {
        "area": {
            "calculate": lambda d: d["side"] ** 2,
            "formula": "مساحت مربع = ضلع²",
            "inputs": ["side"]
        },
        "perimeter": {
            "calculate": lambda d: 4 * d["side"],
            "formula": "محیط مربع = ۴ × ضلع",
            "inputs": ["side"]
        }
    },
    "دایره": {
        "area": {
            "calculate": lambda d: np.pi * (d["radius"] ** 2),
            "formula": "مساحت دایره = π × شعاع²",
            "inputs": ["radius"]
        },
        "perimeter": {
            "calculate": lambda d: 2 * np.pi * d["radius"],
            "formula": "محیط دایره = ۲ × π × شعاع",
            "inputs": ["radius"]
        }
    },
    "چندضلعی منتظم": {
        "area": {
            "calculate": lambda d: (3 * np.sqrt(3) * d["side"] ** 2) / 2,
            "formula": "مساحت شش‌ضلعی منتظم = (۳√۳ × ضلع²) ÷ ۲",
            "inputs": ["side"],
            "extra_info": """
            <div dir="rtl">
                <p><strong>✨ چرا زنبورها از شان عسل شش ضلعی استفاده می‌کنند؟</strong></p>
                <p>شش ضلعی بیشترین استفاده را از فضا می‌کند و هیچ فضایی هدر نمی‌رود. این شکل طبیعی بهترین گزینه برای ذخیره‌سازی عسل است!</p>
                <ul>
                    <li>🔹 استفاده کارآمد از فضا</li>
                    <li>🔹 بیشترین سلول در کوچکترین فضا</li>
                    <li>🔹 قدرت و پایداری بالا</li>
                </ul>
            </div>"""
        },
        "perimeter": {
            "calculate": lambda d: 6 * d["side"],
            "formula": "محیط شش‌ضلعی منتظم = ۶ × ضلع",
            "inputs": ["side"]
        }
    }
}


def calculate(request):
    result = None
    explanation = ""
    extra_info = ""
    shape = request.GET.get('shape', '')
    calc_type = request.GET.get('calc_type', '')

    try:
        if request.method == 'GET' and shape and calc_type:
            shape_data = AREA_PERIMETER_SHAPES.get(shape)

            if shape_data and calc_type in shape_data:
                calc_data = shape_data[calc_type]


                values = {}
                for input_name in calc_data["inputs"]:
                    val = request.GET.get(input_name)
                    if val is not None:
                        values[input_name] = validate_positive_float(val, input_name)

                if len(values) == len(calc_data["inputs"]):
                    result = calc_data["calculate"](values)
                    explanation = calc_data["formula"]

                    if "extra_info" in calc_data:
                        extra_info = calc_data["extra_info"]

    except ValueError as e:
        result = "error"
        explanation = str(e)
    except Exception as e:
        result = "error"
        explanation = f"خطای غیرمنتظره: {str(e)}"

    return render(request, 'calculate.html', {
        'result': result,
        'shape': shape,
        'calc_type': calc_type,
        'explanation': explanation,
        'extra_info': extra_info,
        'side': request.GET.get('side', ''),
        'radius': request.GET.get('radius', ''),
        'base': request.GET.get('base', ''),
        'height': request.GET.get('height', ''),
        'n': request.GET.get('n', '6')
    })


def stats_view(request):
    context = {}

    if request.method == 'POST':
        form = NumbersForm(request.POST)
        if form.is_valid():
            raw_numbers = form.cleaned_data['numbers']
            try:
                number_list = np.array(list(map(float, re.findall(r"[-+]?\d*\.?\d+", raw_numbers))))

                if len(number_list) > 100:
                    context['error'] = "حداکثر می‌توانید ۱۰۰ عدد وارد کنید."
                elif len(number_list) == 0:
                    context['error'] = "حداقل یک عدد وارد کنید."
                else:
                    context['sum'] = float(np.sum(number_list))
                    context['mean'] = float(np.mean(number_list))
                    context['median'] = float(np.median(number_list))


                    try:
                        values, counts = np.unique(number_list, return_counts=True)
                        max_count = np.max(counts)
                        if max_count > 1:
                            modes = values[counts == max_count]
                            if len(modes) == 1:
                                context['mode'] = float(modes[0])
                            else:
                                context['mode'] = f"چند مقدار: {', '.join(map(str, modes))}"
                        else:
                            context['mode'] = "ندارد (همه مقادیر یکبار تکرار شده‌اند)"
                    except Exception:
                        context['mode'] = "قابل محاسبه نیست"

                    context['numbers'] = json.dumps(number_list.tolist())
                    context['number_list'] = number_list.tolist()
                    context['count'] = len(number_list)
                    context['min'] = float(np.min(number_list))
                    context['max'] = float(np.max(number_list))

            except ValueError:
                context['error'] = "مقدار نامعتبر وارد شده است."
        context['form'] = form
    else:
        context['form'] = NumbersForm()

    return render(request, 'mean.html', context)


def calculate_discount(request):
    result = {'show_chart': False}

    if request.method == 'POST':
        mode = request.POST.get('mode')

        try:
            if mode == '1':
                price = validate_positive_float(request.POST.get('price'), "قیمت")
                discount = validate_positive_float(request.POST.get('discount'), "درصد", 100)
                discount_amount = price * (discount / 100)
                final_price = price - discount_amount
                result = {
                    'mode': 1,
                    'show_chart': True,
                    'price': price,
                    'discount': discount,
                    'discount_amount': discount_amount,
                    'final_price': final_price,
                    'chart_discount': discount,
                    'chart_remaining': 100 - discount
                }

            elif mode == '2':
                price = validate_positive_float(request.POST.get('price'), "قیمت اصلی")
                final_price = validate_positive_float(request.POST.get('final_price'), "قیمت نهایی")
                if final_price > price:
                    raise ValueError("قیمت نهایی نمی‌تواند از قیمت اصلی بیشتر باشد.")
                discount = ((price - final_price) / price) * 100
                result = {
                    'mode': 2,
                    'show_chart': True,
                    'price': price,
                    'final_price': final_price,
                    'discount_amount': price - final_price,
                    'discount': discount,
                    'chart_discount': discount,
                    'chart_remaining': 100 - discount
                }

            elif mode == '3':
                discount = validate_positive_float(request.POST.get('discount'), "درصد", 100)
                final_price = validate_positive_float(request.POST.get('final_price'), "قیمت نهایی")
                price = final_price / (1 - discount / 100)
                result = {
                    'mode': 3,
                    'show_chart': True,
                    'discount': discount,
                    'final_price': final_price,
                    'discount_amount': price - final_price,
                    'price': price,
                    'chart_discount': discount,
                    'chart_remaining': 100 - discount
                }

            elif mode == '4':
                a = validate_positive_float(request.POST.get('a'), "عدد اول")
                b = validate_positive_float(request.POST.get('b'), "عدد دوم", 100)
                result = {
                    'mode': 4,
                    'show_chart': False,
                    'a': a,
                    'b': b,
                    'percent': (a * b) / 100
                }

        except Exception as e:
            result['error'] = str(e)

    return render(request, 'discount.html', result)


CONVERSIONS = {
    'meter_to_cm': (100, 'سانتی‌متر', 'متر'),
    'meter_to_mm': (1000, 'میلی‌متر', 'متر'),
    'cm_to_mm': (10, 'میلی‌متر', 'سانتی‌متر'),
    'km_to_m': (1000, 'متر', 'کیلومتر'),
    'm_to_km': (0.001, 'کیلومتر', 'متر'),
    'hour_to_min': (60, 'دقیقه', 'ساعت'),
    'hour_to_sec': (3600, 'ثانیه', 'ساعت'),
    'min_to_sec': (60, 'ثانیه', 'دقیقه'),
    'sec_to_min': (1 / 60, 'دقیقه', 'ثانیه'),
    'min_to_hour': (1 / 60, 'ساعت', 'دقیقه'),
}


def converter_view(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            value = float(request.POST.get('value'))
            conversion_type = request.POST.get('conversion_type')

            if conversion_type in CONVERSIONS:
                multiplier, target_unit, source_unit = CONVERSIONS[conversion_type]
                result = value * multiplier
                return JsonResponse({
                    'result': round(result, 6),
                    'unit': target_unit,
                    'source_unit': source_unit,
                    'target_unit': target_unit,
                    'original_value': value
                })
            else:
                return JsonResponse({'error': 'نوع تبدیل نامعتبر است'}, status=400)

        except (ValueError, TypeError):
            return JsonResponse({'error': 'ورودی نامعتبر. لطفاً یک عدد وارد کنید.'}, status=400)


    conversion_categories = {
        'طول': [
            {'id': 'meter_to_cm', 'name': 'متر به سانتی‌متر', 'from': 'متر', 'to': 'سانتی‌متر'},
            {'id': 'meter_to_mm', 'name': 'متر به میلی‌متر', 'from': 'متر', 'to': 'میلی‌متر'},
            {'id': 'cm_to_mm', 'name': 'سانتی‌متر به میلی‌متر', 'from': 'سانتی‌متر', 'to': 'میلی‌متر'},
            {'id': 'km_to_m', 'name': 'کیلومتر به متر', 'from': 'کیلومتر', 'to': 'متر'},
            {'id': 'm_to_km', 'name': 'متر به کیلومتر', 'from': 'متر', 'to': 'کیلومتر'},
        ],
        'زمان': [
            {'id': 'hour_to_min', 'name': 'ساعت به دقیقه', 'from': 'ساعت', 'to': 'دقیقه'},
            {'id': 'hour_to_sec', 'name': 'ساعت به ثانیه', 'from': 'ساعت', 'to': 'ثانیه'},
            {'id': 'min_to_sec', 'name': 'دقیقه به ثانیه', 'from': 'دقیقه', 'to': 'ثانیه'},
            {'id': 'sec_to_min', 'name': 'ثانیه به دقیقه', 'from': 'ثانیه', 'to': 'دقیقه'},
            {'id': 'min_to_hour', 'name': 'دقیقه به ساعت', 'from': 'دقیقه', 'to': 'ساعت'},
        ]
    }

    return render(request, 'converter.html', {
        'conversion_categories': conversion_categories
    })


import re
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


def linear_equation_view(request):
    return render(request, 'solve_equation.html')


@require_http_methods(["POST"])
def solve_linear_ajax(request):
    try:
        equation = request.POST.get('equation', '').strip()


        equation = equation.replace(' ', '')


        pattern = r'^([+-]?\d*\.?\d*?)x([+-]\d*\.?\d+)?=?0?$'


        match1 = re.match(r'^([+-]?\d*\.?\d*)x([+-]\d*\.?\d+)=0$', equation)


        match2 = re.match(r'^([+-]?\d*\.?\d*)x([+-]\d*\.?\d+)$', equation)


        match3 = re.match(r'^([+-]?\d*\.?\d*)x=0$', equation)


        match4 = re.match(r'^([+-]?\d*\.?\d*)x$', equation)

        a = None
        b = None

        if match1:
            a_str, b_str = match1.groups()
            a = float(a_str) if a_str and a_str not in ['+', '-'] else (
                1 if a_str == '+' else (-1 if a_str == '-' else 1))
            b = float(b_str)
        elif match2:
            a_str, b_str = match2.groups()
            a = float(a_str) if a_str and a_str not in ['+', '-'] else (
                1 if a_str == '+' else (-1 if a_str == '-' else 1))
            b = float(b_str)
        elif match3:
            a_str = match3.group(1)
            a = float(a_str) if a_str and a_str not in ['+', '-'] else (
                1 if a_str == '+' else (-1 if a_str == '-' else 1))
            b = 0
        elif match4:
            a_str = match4.group(1)
            a = float(a_str) if a_str and a_str not in ['+', '-'] else (
                1 if a_str == '+' else (-1 if a_str == '-' else 1))
            b = 0
        else:

            if 'x' not in equation:

                if '=' in equation:
                    parts = equation.split('=')
                    if len(parts) == 2:
                        left = float(parts[0]) if parts[0] else 0
                        right = float(parts[1]) if parts[1] else 0
                        return JsonResponse({
                            'solution': f'معادله ساده: {left} = {right}',
                            'message': f'{left} {"==" if left == right else "≠"} {right}'
                        })

            return JsonResponse({
                'message': 'فرمت معادله نامعتبر است. از فرمت ax+b=0 استفاده کنید. مثال: 2x+4=0'
            }, status=400)


        if a == 0:
            if b == 0:
                return JsonResponse({
                    'solution': '✓ معادله به ازای همه xها برقرار است (نامحدود)',
                    'message': '0x + 0 = 0 → جواب: همه اعداد حقیقی'
                })
            else:
                return JsonResponse({
                    'solution': '✗ معادله جواب ندارد (ناسازگار)',
                    'message': f'{equation} → معادله ناسازگار است'
                })


        x = -b / a


        if x == 0:
            solution_text = 'x = 0'
        elif x == int(x):
            solution_text = f'x = {int(x)}'
        else:
            solution_text = f'x = {round(x, 4)}'


        a_display = '' if a == 1 else ('' if a == -1 else abs(a))
        sign = '-' if a < 0 else ''

        b_sign = '+' if b >= 0 else ''
        b_display = abs(b) if b != 0 else ''

        return JsonResponse({
            'solution': solution_text,
            'message': f'معادله: {equation}\n\n{abs(a) if abs(a) != 1 else ""}x {"+" if b >= 0 else "-"} {abs(b) if b != 0 else "0"} = 0\n\n→ {abs(a) if abs(a) != 1 else ""}x = {-b}\n\n→ x = {-b} / {a}\n\n→ {solution_text}'
        })

    except ValueError as e:
        return JsonResponse({
            'message': 'مقادیر وارد شده معتبر نیستند. لطفاً اعداد صحیح یا اعشاری وارد کنید.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'message': f'خطا در پردازش معادله: {str(e)}'
        }, status=400)
