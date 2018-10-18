
var gulp = require('gulp')
var cssnano = require('gulp-cssnano')
var rename = require('gulp-rename')
var uglify = require('gulp-uglify');
gulp.task('css', function(){
    gulp.src('./css/*.css')
        .pipe(cssnano()) //压缩css
        .pipe(rename({'suffix':'.min'})) //添加前缀
        .pipe(gulp.dest('./css/dist/'))
})

gulp.task('javascript', function() {
    // 1. 找到文件
    gulp.src('node_modules/jquery/dist/jquery.js')
    // 2. 压缩文件
    .pipe(uglify({ mangle: false }))
    .pipe(rename({'suffix':'.min'})) //添加前缀
    // 3. 另存压缩后的文件
    .pipe(gulp.dest('js/'))
})